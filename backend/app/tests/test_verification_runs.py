import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.lab_instance import LabInstance, LabNode
from app.models.lab_template import LabTemplate
from app.tests.test_tickets import ticket_payload
from app.tests.test_verification_rules import rule_payload


async def create_published_ticket_with_rule(client, auth_header, admin_token, template_id: str) -> dict:
    ticket = await client.post(
        "/api/v1/tickets",
        headers=auth_header(admin_token),
        json=ticket_payload(template_id, "Run Verify Ticket"),
    )
    await client.post(f"/api/v1/tickets/{ticket.json()['id']}/publish", headers=auth_header(admin_token))
    await client.post(
        f"/api/v1/tickets/{ticket.json()['id']}/verification-rules",
        headers=auth_header(admin_token),
        json=rule_payload(),
    )
    return ticket.json()


@pytest.mark.asyncio
async def test_verification_rejects_if_lab_not_running(
    client: AsyncClient,
    auth_header,
    admin_token: str,
    student_token: str,
    active_template: LabTemplate,
) -> None:
    ticket = await create_published_ticket_with_rule(client, auth_header, admin_token, str(active_template.id))
    attempt = await client.post(f"/api/v1/tickets/{ticket['id']}/start", headers=auth_header(student_token))

    response = await client.post(
        f"/api/v1/my/attempts/{attempt.json()['id']}/verify",
        headers=auth_header(student_token),
    )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_student_can_queue_verification_for_own_running_attempt(
    client: AsyncClient,
    auth_header,
    admin_token: str,
    student_token: str,
    active_template: LabTemplate,
    session_factory: async_sessionmaker[AsyncSession],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class DummyTask:
        def delay(self, run_id: str) -> None:
            return None

    monkeypatch.setattr("app.workers.verification_tasks.run_verification_task", DummyTask())
    ticket = await create_published_ticket_with_rule(client, auth_header, admin_token, str(active_template.id))
    attempt = await client.post(f"/api/v1/tickets/{ticket['id']}/start", headers=auth_header(student_token))
    async with session_factory() as session:
        lab = await session.get(LabInstance, uuid.UUID(attempt.json()["lab_instance_id"]))
        assert lab is not None
        lab.status = "RUNNING"
        session.add(
            LabNode(
                lab_instance_id=lab.id,
                name="host1",
                kind="linux",
                container_name="clab-test-host1",
                management_ipv4="172.20.20.2/24",
                status="running",
            )
        )
        await session.commit()

    response = await client.post(
        f"/api/v1/my/attempts/{attempt.json()['id']}/verify",
        headers=auth_header(student_token),
    )

    assert response.status_code == 201
    assert response.json()["status"] == "QUEUED"


@pytest.mark.asyncio
async def test_student_cannot_run_verification_for_another_students_attempt(
    client: AsyncClient,
    auth_header,
    admin_token: str,
    student_token: str,
    active_template: LabTemplate,
) -> None:
    await client.post(
        "/api/v1/users",
        headers=auth_header(admin_token),
        json={
            "email": "verify-other@example.com",
            "username": "verifyother",
            "password": "OtherPassword123!",
            "full_name": "Verify Other",
            "role": "STUDENT",
            "is_active": True,
        },
    )
    other_login = await client.post("/api/v1/auth/login", json={"username": "verifyother", "password": "OtherPassword123!"})
    other_token = other_login.json()["access_token"]
    ticket = await create_published_ticket_with_rule(client, auth_header, admin_token, str(active_template.id))
    attempt = await client.post(f"/api/v1/tickets/{ticket['id']}/start", headers=auth_header(other_token))

    response = await client.post(
        f"/api/v1/my/attempts/{attempt.json()['id']}/verify",
        headers=auth_header(student_token),
    )

    assert response.status_code == 403
