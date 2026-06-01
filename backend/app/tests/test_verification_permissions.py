import pytest
from httpx import AsyncClient

from app.models.lab_template import LabTemplate
from app.tests.test_tickets import ticket_payload
from app.tests.test_verification_rules import rule_payload


@pytest.mark.asyncio
async def test_instructor_cannot_create_rule_for_another_instructors_ticket(
    client: AsyncClient,
    auth_header,
    instructor_token: str,
    active_template: LabTemplate,
) -> None:
    created = await client.post(
        "/api/v1/tickets",
        headers=auth_header(instructor_token),
        json=ticket_payload(str(active_template.id), "Instructor Owned Verify Ticket"),
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"username": "instructor2", "password": "InstructorPassword123!"},
    )
    instructor2_token = login.json()["access_token"]

    response = await client.post(
        f"/api/v1/tickets/{created.json()['id']}/verification-rules",
        headers=auth_header(instructor2_token),
        json=rule_payload(),
    )

    assert response.status_code == 403
