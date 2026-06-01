import pytest
from httpx import AsyncClient

from app.models.lab_template import LabTemplate


@pytest.mark.asyncio
async def test_student_cannot_view_another_students_lab(
    client: AsyncClient,
    auth_header,
    admin_token: str,
    student_token: str,
    active_template: LabTemplate,
) -> None:
    create_user = await client.post(
        "/api/v1/users",
        headers=auth_header(admin_token),
        json={
            "email": "other@example.com",
            "username": "otherstudent",
            "password": "OtherPassword123!",
            "full_name": "Other Student",
            "role": "STUDENT",
            "is_active": True,
        },
    )
    assert create_user.status_code == 201
    login = await client.post(
        "/api/v1/auth/login",
        json={"username": "otherstudent", "password": "OtherPassword123!"},
    )
    other_token = login.json()["access_token"]
    lab = await client.post(
        "/api/v1/labs",
        headers=auth_header(other_token),
        json={"template_id": str(active_template.id)},
    )

    response = await client.get(f"/api/v1/labs/{lab.json()['id']}", headers=auth_header(student_token))

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_view_all_labs(
    client: AsyncClient,
    auth_header,
    admin_token: str,
    student_token: str,
    active_template: LabTemplate,
) -> None:
    await client.post(
        "/api/v1/labs",
        headers=auth_header(student_token),
        json={"template_id": str(active_template.id)},
    )

    response = await client.get("/api/v1/labs", headers=auth_header(admin_token))

    assert response.status_code == 200
    assert len(response.json()) == 1
