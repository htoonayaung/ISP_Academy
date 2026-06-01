from httpx import AsyncClient

from app.models.user import User


async def test_student_cannot_list_users(
    client: AsyncClient,
    student_token: str,
    auth_header,
) -> None:
    response = await client.get("/api/v1/users", headers=auth_header(student_token))

    assert response.status_code == 403


async def test_instructor_can_list_students_only(
    client: AsyncClient,
    instructor_token: str,
    auth_header,
) -> None:
    response = await client.get("/api/v1/users", headers=auth_header(instructor_token))

    assert response.status_code == 200
    payload = response.json()
    assert payload
    assert {user["role"] for user in payload} == {"STUDENT"}


async def test_instructor_can_view_students_only(
    client: AsyncClient,
    instructor_token: str,
    seeded_users: dict[str, User],
    auth_header,
) -> None:
    student_response = await client.get(
        f"/api/v1/users/{seeded_users['student'].id}",
        headers=auth_header(instructor_token),
    )
    admin_response = await client.get(
        f"/api/v1/users/{seeded_users['admin'].id}",
        headers=auth_header(instructor_token),
    )

    assert student_response.status_code == 200
    assert admin_response.status_code == 403


async def test_non_admin_cannot_escalate_role(
    client: AsyncClient,
    student_token: str,
    seeded_users: dict[str, User],
    auth_header,
) -> None:
    response = await client.patch(
        f"/api/v1/users/{seeded_users['student'].id}",
        headers=auth_header(student_token),
        json={"role": "ADMIN"},
    )

    assert response.status_code == 403

