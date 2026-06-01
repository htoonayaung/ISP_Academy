import pytest
from httpx import ASGITransport, AsyncClient

from app.api.v1 import system
from app.main import app


@pytest.mark.asyncio
async def test_ready_returns_ok_when_dependencies_are_available(monkeypatch: pytest.MonkeyPatch) -> None:
    async def postgres_ok() -> bool:
        return True

    async def redis_ok() -> bool:
        return True

    monkeypatch.setattr(system, "check_postgres", postgres_ok)
    monkeypatch.setattr(system, "check_redis", redis_ok)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "components": {
            "postgresql": "ok",
            "redis": "ok",
        },
    }


@pytest.mark.asyncio
async def test_ready_returns_503_when_dependency_is_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    async def postgres_ok() -> bool:
        return True

    async def redis_error() -> bool:
        return False

    monkeypatch.setattr(system, "check_postgres", postgres_ok)
    monkeypatch.setattr(system, "check_redis", redis_error)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "components": {
            "postgresql": "ok",
            "redis": "error",
        },
    }

