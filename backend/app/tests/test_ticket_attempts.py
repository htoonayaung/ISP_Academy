import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.lab_instance import LabInstance
from app.models.lab_template import LabTemplate
from app.tests.test_tickets import ticket_payload


@pytest.mark.asyncio
async def test_student_can_start_attempt_from_published_ticket(
    client: AsyncClient,
    auth_header,
    admin_token: str,
    student_token: str,
    active_template: LabTemplate,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    created = await client.post(
        "/api/v1/tickets",
        headers=auth_header(admin_token),
        json=ticket_payload(str(active_template.id)),
    )
    await client.post(f"/api/v1/tickets/{created.json()['id']}/publish", headers=auth_header(admin_token))

    response = await client.post(
        f"/api/v1/tickets/{created.json()['id']}/start",
        headers=auth_header(student_token),
    )

    assert response.status_code == 201
    attempt = response.json()
    assert attempt["ticket_id"] == created.json()["id"]
    assert attempt["status"] == "STARTED"
    async with session_factory() as session:
        lab = await session.get(LabInstance, uuid.UUID(attempt["lab_instance_id"]))
        assert lab is not None
        assert lab.status == "CREATED"


@pytest.mark.asyncio
async def test_student_cannot_start_attempt_from_draft_or_archived_ticket(
    client: AsyncClient,
    auth_header,
    admin_token: str,
    student_token: str,
    active_template: LabTemplate,
) -> None:
    draft = await client.post(
        "/api/v1/tickets",
        headers=auth_header(admin_token),
        json=ticket_payload(str(active_template.id), "Draft Attempt Ticket"),
    )
    archived = await client.post(
        "/api/v1/tickets",
        headers=auth_header(admin_token),
        json=ticket_payload(str(active_template.id), "Archived Attempt Ticket"),
    )
    await client.post(f"/api/v1/tickets/{archived.json()['id']}/publish", headers=auth_header(admin_token))
    await client.post(f"/api/v1/tickets/{archived.json()['id']}/archive", headers=auth_header(admin_token))

    draft_start = await client.post(
        f"/api/v1/tickets/{draft.json()['id']}/start",
        headers=auth_header(student_token),
    )
    archived_start = await client.post(
        f"/api/v1/tickets/{archived.json()['id']}/start",
        headers=auth_header(student_token),
    )

    assert draft_start.status_code == 404
    assert archived_start.status_code == 404


@pytest.mark.asyncio
async def test_student_cannot_view_another_students_attempt(
    client: AsyncClient,
    auth_header,
    admin_token: str,
    active_template: LabTemplate,
) -> None:
    await client.post(
        "/api/v1/users",
        headers=auth_header(admin_token),
        json={
            "email": "attempt-other@example.com",
            "username": "attemptother",
            "password": "OtherPassword123!",
            "full_name": "Attempt Other",
            "role": "STUDENT",
            "is_active": True,
        },
    )
    first_login = await client.post(
        "/api/v1/auth/login",
        json={"username": "student", "password": "StudentPassword123!"},
    )
    second_login = await client.post(
        "/api/v1/auth/login",
        json={"username": "attemptother", "password": "OtherPassword123!"},
    )
    first_token = first_login.json()["access_token"]
    second_token = second_login.json()["access_token"]
    ticket = await client.post(
        "/api/v1/tickets",
        headers=auth_header(admin_token),
        json=ticket_payload(str(active_template.id), "Private Attempt Ticket"),
    )
    await client.post(f"/api/v1/tickets/{ticket.json()['id']}/publish", headers=auth_header(admin_token))
    attempt = await client.post(f"/api/v1/tickets/{ticket.json()['id']}/start", headers=auth_header(first_token))

    response = await client.get(
        f"/api/v1/my/attempts/{attempt.json()['id']}",
        headers=auth_header(second_token),
    )

    assert response.status_code == 403
