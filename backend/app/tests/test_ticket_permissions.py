import pytest
from httpx import AsyncClient

from app.models.lab_template import LabTemplate
from app.tests.test_tickets import ticket_payload


@pytest.mark.asyncio
async def test_instructor_cannot_update_another_instructors_ticket(
    client: AsyncClient,
    auth_header,
    instructor_token: str,
    active_template: LabTemplate,
) -> None:
    created = await client.post(
        "/api/v1/tickets",
        headers=auth_header(instructor_token),
        json=ticket_payload(str(active_template.id), "Owner Ticket"),
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"username": "instructor2", "password": "InstructorPassword123!"},
    )
    instructor2_token = login.json()["access_token"]

    response = await client.patch(
        f"/api/v1/tickets/{created.json()['id']}",
        headers=auth_header(instructor2_token),
        json={"title": "Stolen Ticket"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_student_sees_only_published_tickets(
    client: AsyncClient,
    auth_header,
    admin_token: str,
    student_token: str,
    active_template: LabTemplate,
) -> None:
    draft = await client.post(
        "/api/v1/tickets",
        headers=auth_header(admin_token),
        json=ticket_payload(str(active_template.id), "Draft Ticket"),
    )
    published = await client.post(
        "/api/v1/tickets",
        headers=auth_header(admin_token),
        json=ticket_payload(str(active_template.id), "Published Ticket"),
    )
    archived = await client.post(
        "/api/v1/tickets",
        headers=auth_header(admin_token),
        json=ticket_payload(str(active_template.id), "Archived Ticket"),
    )
    await client.post(f"/api/v1/tickets/{published.json()['id']}/publish", headers=auth_header(admin_token))
    await client.post(f"/api/v1/tickets/{archived.json()['id']}/publish", headers=auth_header(admin_token))
    await client.post(f"/api/v1/tickets/{archived.json()['id']}/archive", headers=auth_header(admin_token))

    response = await client.get("/api/v1/tickets", headers=auth_header(student_token))

    assert response.status_code == 200
    titles = {ticket["title"] for ticket in response.json()}
    assert titles == {"Published Ticket"}

    draft_detail = await client.get(f"/api/v1/tickets/{draft.json()['id']}", headers=auth_header(student_token))
    archived_detail = await client.get(f"/api/v1/tickets/{archived.json()['id']}", headers=auth_header(student_token))
    assert draft_detail.status_code == 404
    assert archived_detail.status_code == 404
