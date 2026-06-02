import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.core.permissions import get_current_admin
from app.models.user import User
from app.repositories.labs import LabRepository
from app.schemas.admin_runtime import (
    RuntimeCleanupRead,
    RuntimeCleanupRequest,
    RuntimeEventsRead,
    RuntimeRecoverRead,
    RuntimeRecoverRequest,
    RuntimeRefreshRead,
    RuntimeStatusRead,
)
from app.services.admin_runtime_service import AdminRuntimeService

router = APIRouter(tags=["admin-runtime"])


def get_admin_runtime_service(session: AsyncSession = Depends(get_db_session)) -> AdminRuntimeService:
    return AdminRuntimeService(LabRepository(session))


@router.get("/labs/status", response_model=RuntimeStatusRead)
async def get_runtime_status(
    _: User = Depends(get_current_admin),
    service: AdminRuntimeService = Depends(get_admin_runtime_service),
) -> RuntimeStatusRead:
    return await service.get_status()


@router.post("/labs/refresh", response_model=RuntimeRefreshRead)
async def refresh_runtime_labs(
    _: User = Depends(get_current_admin),
    service: AdminRuntimeService = Depends(get_admin_runtime_service),
) -> RuntimeRefreshRead:
    queued, statuses, warnings = await service.refresh()
    return RuntimeRefreshRead(queued_refresh_count=queued, inspected_statuses=statuses, warnings=warnings)


@router.post("/labs/{lab_id}/recover", response_model=RuntimeRecoverRead)
async def recover_runtime_lab(
    lab_id: uuid.UUID,
    payload: RuntimeRecoverRequest,
    current_user: User = Depends(get_current_admin),
    service: AdminRuntimeService = Depends(get_admin_runtime_service),
) -> RuntimeRecoverRead:
    return await service.recover(current_user, lab_id, payload.action, payload.confirm)


@router.post("/cleanup/demo", response_model=RuntimeCleanupRead)
async def cleanup_demo_runtime(
    payload: RuntimeCleanupRequest,
    _: User = Depends(get_current_admin),
    service: AdminRuntimeService = Depends(get_admin_runtime_service),
) -> RuntimeCleanupRead:
    if payload.confirm != "CLEANUP_DEMO_RUNTIME":
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Typed confirmation CLEANUP_DEMO_RUNTIME is required",
        )
    return await service.cleanup_demo_runtime()


@router.get("/labs/{lab_id}/events", response_model=RuntimeEventsRead)
async def get_runtime_lab_events(
    lab_id: uuid.UUID,
    _: User = Depends(get_current_admin),
    service: AdminRuntimeService = Depends(get_admin_runtime_service),
) -> RuntimeEventsRead:
    return RuntimeEventsRead(lab_id=lab_id, events=await service.list_events(lab_id))
