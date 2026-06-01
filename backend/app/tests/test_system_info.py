import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_system_info_returns_foundation_components() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/system/info")

    assert response.status_code == 200
    payload = response.json()

    assert payload["app_name"] == "AI-Powered ISP Academy MVP"
    assert payload["version"] == "0.1.0"
    assert payload["environment"] == "testing"
    assert payload["components"] == {
        "fastapi": True,
        "postgresql": True,
        "sqlalchemy_async": True,
        "alembic": True,
        "redis": True,
        "celery": True,
    }

