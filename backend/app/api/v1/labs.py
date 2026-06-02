import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.core.permissions import get_current_user
from app.models.lab_instance import LabEvent, LabInstance, LabNode
from app.models.user import User
from app.repositories.lab_templates import LabTemplateRepository
from app.repositories.labs import LabRepository
from app.schemas.lab_instance import LabCreate, LabEventRead, LabNodeRead, LabRead, LabStatusRead
from app.services.lab_service import LabService

router = APIRouter(tags=["labs"])


def get_lab_service(session: AsyncSession = Depends(get_db_session)) -> LabService:
    return LabService(LabRepository(session), LabTemplateRepository(session))


@router.post("", response_model=LabRead, status_code=status.HTTP_201_CREATED)
async def create_lab(
    payload: LabCreate,
    current_user: User = Depends(get_current_user),
    service: LabService = Depends(get_lab_service),
) -> LabInstance:
    return await service.create_lab(current_user, payload)


@router.get("", response_model=list[LabRead])
async def list_labs(
    current_user: User = Depends(get_current_user),
    service: LabService = Depends(get_lab_service),
) -> list[LabInstance]:
    return await service.list_labs(current_user)


@router.get("/{lab_id}", response_model=LabRead)
async def get_lab(
    lab_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: LabService = Depends(get_lab_service),
) -> LabInstance:
    return await service.get_lab(current_user, lab_id)


@router.post("/{lab_id}/start", response_model=LabRead)
async def start_lab(
    lab_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: LabService = Depends(get_lab_service),
) -> LabInstance:
    return await service.start_lab(current_user, lab_id)


@router.post("/{lab_id}/stop", response_model=LabRead)
async def stop_lab(
    lab_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: LabService = Depends(get_lab_service),
) -> LabInstance:
    return await service.stop_lab(current_user, lab_id)


@router.post("/{lab_id}/destroy", response_model=LabRead)
async def destroy_lab(
    lab_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: LabService = Depends(get_lab_service),
) -> LabInstance:
    return await service.destroy_lab(current_user, lab_id)


@router.delete("/{lab_id}/hard-delete", status_code=status.HTTP_204_NO_CONTENT)
async def hard_delete_lab(
    lab_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: LabService = Depends(get_lab_service),
) -> None:
    await service.hard_delete_lab(current_user, lab_id)


@router.get("/{lab_id}/status", response_model=LabStatusRead)
async def get_lab_status(
    lab_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: LabService = Depends(get_lab_service),
) -> LabStatusRead:
    lab = await service.get_lab(current_user, lab_id)
    return service.shape_lab_status(current_user, lab)


@router.get("/{lab_id}/nodes", response_model=list[LabNodeRead])
async def list_lab_nodes(
    lab_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: LabService = Depends(get_lab_service),
) -> list[LabNode]:
    return await service.list_nodes(current_user, lab_id)


@router.get("/{lab_id}/events", response_model=list[LabEventRead])
async def list_lab_events(
    lab_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: LabService = Depends(get_lab_service),
) -> list[LabEvent]:
    return await service.list_events(current_user, lab_id)
