from httpx import AsyncClient

from app.models.user import User


async def test_login_success(client: AsyncClient, seeded_users: dict[str, User]) -> None:
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "AdminPassword123!"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["expires_in"] == 1800
    assert isinstance(payload["access_token"], str)


async def test_login_wrong_credentials_uses_consistent_error(
    client: AsyncClient,
    seeded_users: dict[str, User],
) -> None:
    missing_response = await client.post(
        "/api/v1/auth/login",
        json={"username": "missing", "password": "WrongPassword123!"},
    )
    wrong_password_response = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "WrongPassword123!"},
    )

    assert missing_response.status_code == 401
    assert wrong_password_response.status_code == 401
    assert missing_response.json()["detail"] == "Invalid username or password"
    assert wrong_password_response.json()["detail"] == "Invalid username or password"


async def test_inactive_user_cannot_login(client: AsyncClient, seeded_users: dict[str, User]) -> None:
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "inactive", "password": "InactivePassword123!"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"


async def test_auth_me_returns_current_user_without_hashed_password(
    client: AsyncClient,
    admin_token: str,
    auth_header,
) -> None:
    response = await client.get("/api/v1/auth/me", headers=auth_header(admin_token))

    assert response.status_code == 200
    payload = response.json()["user"]
    assert payload["email"] == "admin@example.com"
    assert payload["role"] == "ADMIN"
    assert "hashed_password" not in payload

