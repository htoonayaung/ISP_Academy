import pytest
from httpx import AsyncClient

from app.models.lab_template import LabTemplate
from app.tests.test_tickets import ticket_payload


def rule_payload(target_node: str = "host1", command: str = "echo ok") -> dict:
    return {
        "name": "Check output",
        "target_node": target_node,
        "command": command,
        "parser_type": "SIMPLE_TEXT",
        "assertion_type": "CONTAINS",
        "expected_value": "ok",
        "timeout_seconds": 5,
        "is_active": True,
    }


async def create_ticket(client: AsyncClient, token: str, auth_header, template_id: str, title: str = "Verify Ticket") -> dict:
    response = await client.post(
        "/api/v1/tickets",
        headers=auth_header(token),
        json=ticket_payload(template_id, title),
    )
    return response.json()


@pytest.mark.asyncio
async def test_admin_can_create_verification_rule(
    client: AsyncClient,
    auth_header,
    admin_token: str,
    active_template: LabTemplate,
) -> None:
    ticket = await create_ticket(client, admin_token, auth_header, str(active_template.id))

    response = await client.post(
        f"/api/v1/tickets/{ticket['id']}/verification-rules",
        headers=auth_header(admin_token),
        json=rule_payload(),
    )

    assert response.status_code == 201
    assert response.json()["command"] == "echo ok"


@pytest.mark.asyncio
async def test_instructor_can_create_rule_for_own_ticket(
    client: AsyncClient,
    auth_header,
    instructor_token: str,
    active_template: LabTemplate,
) -> None:
    ticket = await create_ticket(client, instructor_token, auth_header, str(active_template.id), "Own Verify Ticket")

    response = await client.post(
        f"/api/v1/tickets/{ticket['id']}/verification-rules",
        headers=auth_header(instructor_token),
        json=rule_payload(),
    )

    assert response.status_code == 201


@pytest.mark.asyncio
async def test_student_cannot_create_verification_rule(
    client: AsyncClient,
    auth_header,
    admin_token: str,
    student_token: str,
    active_template: LabTemplate,
) -> None:
    ticket = await create_ticket(client, admin_token, auth_header, str(active_template.id))

    response = await client.post(
        f"/api/v1/tickets/{ticket['id']}/verification-rules",
        headers=auth_header(student_token),
        json=rule_payload(),
    )

    assert response.status_code == 403
