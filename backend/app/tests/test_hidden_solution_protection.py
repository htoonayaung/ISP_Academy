import pytest
from httpx import AsyncClient

from app.models.lab_template import LabTemplate
from app.tests.test_tickets import ticket_payload


@pytest.mark.asyncio
async def test_student_ticket_response_excludes_hidden_solution(
    client: AsyncClient,
    auth_header,
    admin_token: str,
    student_token: str,
    active_template: LabTemplate,
) -> None:
    created = await client.post(
        "/api/v1/tickets",
        headers=auth_header(admin_token),
        json=ticket_payload(str(active_template.id)),
    )
    await client.post(f"/api/v1/tickets/{created.json()['id']}/publish", headers=auth_header(admin_token))

    list_response = await client.get("/api/v1/tickets", headers=auth_header(student_token))
    detail_response = await client.get(
        f"/api/v1/tickets/{created.json()['id']}",
        headers=auth_header(student_token),
    )

    assert "hidden_solution" not in list_response.json()[0]
    assert "hidden_solution" not in detail_response.json()


@pytest.mark.asyncio
async def test_admin_and_owner_instructor_can_see_hidden_solution(
    client: AsyncClient,
    auth_header,
    admin_token: str,
    instructor_token: str,
    active_template: LabTemplate,
) -> None:
    admin_ticket = await client.post(
        "/api/v1/tickets",
        headers=auth_header(admin_token),
        json=ticket_payload(str(active_template.id), "Admin Ticket"),
    )
    instructor_ticket = await client.post(
        "/api/v1/tickets",
        headers=auth_header(instructor_token),
        json=ticket_payload(str(active_template.id), "Instructor Ticket"),
    )

    admin_view = await client.get(
        f"/api/v1/tickets/{admin_ticket.json()['id']}",
        headers=auth_header(admin_token),
    )
    instructor_view = await client.get(
        f"/api/v1/tickets/{instructor_ticket.json()['id']}",
        headers=auth_header(instructor_token),
    )

    assert admin_view.json()["hidden_solution"] == "Enable the missing interface."
    assert instructor_view.json()["hidden_solution"] == "Enable the missing interface."
