from httpx import AsyncClient

from app.models.user import User


async def test_admin_can_create_user(
    client: AsyncClient,
    admin_token: str,
    auth_header,
) -> None:
    response = await client.post(
        "/api/v1/users",
        headers=auth_header(admin_token),
        json={
            "email": "new.student@example.com",
            "username": "newstudent",
            "password": "NewStudentPassword123!",
            "full_name": "New Student",
            "role": "STUDENT",
            "is_active": True,
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["email"] == "new.student@example.com"
    assert payload["role"] == "STUDENT"
    assert "hashed_password" not in payload


async def test_hashed_password_is_never_returned_in_user_list(
    client: AsyncClient,
    admin_token: str,
    auth_header,
) -> None:
    response = await client.get("/api/v1/users", headers=auth_header(admin_token))

    assert response.status_code == 200
    assert response.json()
    assert all("hashed_password" not in user for user in response.json())


async def test_student_can_view_only_own_profile(
    client: AsyncClient,
    student_token: str,
    seeded_users: dict[str, User],
    auth_header,
) -> None:
    own_response = await client.get(
        f"/api/v1/users/{seeded_users['student'].id}",
        headers=auth_header(student_token),
    )
    other_response = await client.get(
        f"/api/v1/users/{seeded_users['admin'].id}",
        headers=auth_header(student_token),
    )

    assert own_response.status_code == 200
    assert other_response.status_code == 403


async def test_admin_can_deactivate_user(
    client: AsyncClient,
    admin_token: str,
    seeded_users: dict[str, User],
    auth_header,
) -> None:
    response = await client.delete(
        f"/api/v1/users/{seeded_users['student'].id}",
        headers=auth_header(admin_token),
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is False


async def test_admin_cannot_deactivate_self(
    client: AsyncClient,
    admin_token: str,
    seeded_users: dict[str, User],
    auth_header,
) -> None:
    response = await client.delete(
        f"/api/v1/users/{seeded_users['admin'].id}",
        headers=auth_header(admin_token),
    )

    assert response.status_code == 409


async def test_admin_can_reactivate_user_with_patch(
    client: AsyncClient,
    admin_token: str,
    seeded_users: dict[str, User],
    auth_header,
) -> None:
    response = await client.patch(
        f"/api/v1/users/{seeded_users['inactive'].id}",
        headers=auth_header(admin_token),
        json={"is_active": True},
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is True


async def test_admin_can_reset_password_without_returning_plaintext(
    client: AsyncClient,
    admin_token: str,
    seeded_users: dict[str, User],
    auth_header,
) -> None:
    reset_response = await client.post(
        f"/api/v1/users/{seeded_users['student'].id}/reset-password",
        headers=auth_header(admin_token),
        json={"new_password": "ResetPassword123!"},
    )
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"username": "student", "password": "ResetPassword123!"},
    )

    assert reset_response.status_code == 200
    assert "ResetPassword123!" not in reset_response.text
    assert "hashed_password" not in reset_response.json()
    assert login_response.status_code == 200


async def test_student_cannot_reset_password(
    client: AsyncClient,
    student_token: str,
    seeded_users: dict[str, User],
    auth_header,
) -> None:
    response = await client.post(
        f"/api/v1/users/{seeded_users['admin'].id}/reset-password",
        headers=auth_header(student_token),
        json={"new_password": "ResetPassword123!"},
    )

    assert response.status_code == 403
