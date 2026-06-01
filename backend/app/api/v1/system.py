from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from redis.asyncio import Redis
from sqlalchemy import text

from app.core.config import get_settings
from app.db.session import async_session_factory

router = APIRouter(tags=["system"])


async def check_postgres() -> bool:
    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


async def check_redis() -> bool:
    settings = get_settings()
    client = Redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
    try:
        response = await client.ping()
        return bool(response)
    except Exception:
        return False
    finally:
        await client.aclose()


@router.get("/health")
async def health() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
    }


@router.get("/ready")
async def ready() -> JSONResponse:
    postgres_ready = await check_postgres()
    redis_ready = await check_redis()
    is_ready = postgres_ready and redis_ready

    payload = {
        "status": "ready" if is_ready else "not_ready",
        "components": {
            "postgresql": "ok" if postgres_ready else "error",
            "redis": "ok" if redis_ready else "error",
        },
    }

    return JSONResponse(
        status_code=status.HTTP_200_OK if is_ready else status.HTTP_503_SERVICE_UNAVAILABLE,
        content=payload,
    )


@router.get("/api/v1/system/info")
async def system_info() -> dict[str, object]:
    settings = get_settings()
    return {
        "app_name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "components": {
            "fastapi": True,
            "postgresql": True,
            "sqlalchemy_async": True,
            "alembic": True,
            "redis": True,
            "celery": True,
        },
    }

