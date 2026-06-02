from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.core.config import get_settings
from app.core.permissions import get_current_user
from app.models.user import User
from app.repositories.demo import DemoRepository
from app.schemas.demo import DemoResetRequest, DemoResetResponse, DemoSetupRequest, DemoSetupResponse, DemoSetupStatusRead
from app.services.demo_setup_service import DemoSetupService

router = APIRouter(tags=["admin-demo"])


def get_demo_setup_service(session: AsyncSession = Depends(get_db_session)) -> DemoSetupService:
    return DemoSetupService(repository=DemoRepository(session), settings=get_settings())


@router.get("/status", response_model=DemoSetupStatusRead)
async def get_demo_status(
    current_user: User = Depends(get_current_user),
    service: DemoSetupService = Depends(get_demo_setup_service),
) -> DemoSetupStatusRead:
    return await service.status(current_user)


@router.post("/setup", response_model=DemoSetupResponse)
async def run_demo_setup(
    payload: DemoSetupRequest,
    current_user: User = Depends(get_current_user),
    service: DemoSetupService = Depends(get_demo_setup_service),
) -> DemoSetupResponse:
    return await service.setup(current_user, payload)


@router.post("/reset", response_model=DemoResetResponse)
async def reset_demo_data(
    payload: DemoResetRequest,
    current_user: User = Depends(get_current_user),
    service: DemoSetupService = Depends(get_demo_setup_service),
) -> DemoResetResponse:
    return await service.reset(current_user, payload.confirm, payload.destroy_demo_labs)
