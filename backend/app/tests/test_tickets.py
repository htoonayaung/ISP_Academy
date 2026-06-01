import pytest
from httpx import AsyncClient

from app.models.lab_template import LabTemplate


def ticket_payload(template_id: str, title: str = "BGP Neighbor Down") -> dict:
    return {
        "lab_template_id": template_id,
        "title": title,
        "description": "Troubleshoot a simple ISP ticket.",
        "student_instructions": "Find why reachability is broken.",
        "hints": "Check interface status first.",
        "hidden_solution": "Enable the missing interface.",
        "status": "DRAFT",
    }


@pytest.mark.asyncio
async def test_admin_can_create_ticket(
    client: AsyncClient,
    auth_header,
    admin_token: str,
    active_template: LabTemplate,
) -> None:
    response = await client.post(
        "/api/v1/tickets",
        headers=auth_header(admin_token),
        json=ticket_payload(str(active_template.id)),
    )

    assert response.status_code == 201
    assert response.json()["title"] == "BGP Neighbor Down"
    assert response.json()["status"] == "DRAFT"
    assert response.json()["hidden_solution"] == "Enable the missing interface."


@pytest.mark.asyncio
async def test_instructor_can_create_ticket(
    client: AsyncClient,
    auth_header,
    instructor_token: str,
    active_template: LabTemplate,
) -> None:
    response = await client.post(
        "/api/v1/tickets",
        headers=auth_header(instructor_token),
        json=ticket_payload(str(active_template.id), "OSPF Ticket"),
    )

    assert response.status_code == 201
    assert response.json()["title"] == "OSPF Ticket"


@pytest.mark.asyncio
async def test_student_cannot_create_ticket(
    client: AsyncClient,
    auth_header,
    student_token: str,
    active_template: LabTemplate,
) -> None:
    response = await client.post(
        "/api/v1/tickets",
        headers=auth_header(student_token),
        json=ticket_payload(str(active_template.id)),
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_publish_ticket(
    client: AsyncClient,
    auth_header,
    admin_token: str,
    active_template: LabTemplate,
) -> None:
    created = await client.post(
        "/api/v1/tickets",
        headers=auth_header(admin_token),
        json=ticket_payload(str(active_template.id)),
    )

    response = await client.post(
        f"/api/v1/tickets/{created.json()['id']}/publish",
        headers=auth_header(admin_token),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "PUBLISHED"
    assert response.json()["published_at"] is not None
