import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.core.permissions import get_current_user
from app.models.lab_template import LabTemplate
from app.models.user import User
from app.repositories.lab_templates import LabTemplateRepository
from app.schemas.lab_template import (
    LabTemplateCreate,
    LabTemplateRead,
    LabTemplateUpdate,
    LabTemplateValidationResult,
)
from app.schemas.topology import TopologyRead
from app.services.lab_template_service import LabTemplateService
from app.services.topology_parser import TopologyParser

router = APIRouter(tags=["lab-templates"])


def get_lab_template_service(session: AsyncSession = Depends(get_db_session)) -> LabTemplateService:
    return LabTemplateService(LabTemplateRepository(session))


@router.post("", response_model=LabTemplateRead, status_code=status.HTTP_201_CREATED)
async def create_lab_template(
    payload: LabTemplateCreate,
    current_user: User = Depends(get_current_user),
    service: LabTemplateService = Depends(get_lab_template_service),
) -> LabTemplate:
    return await service.create_template(current_user, payload)


@router.get("", response_model=list[LabTemplateRead])
async def list_lab_templates(
    current_user: User = Depends(get_current_user),
    service: LabTemplateService = Depends(get_lab_template_service),
) -> list[LabTemplate]:
    return await service.list_templates(current_user)


@router.get("/{template_id}", response_model=LabTemplateRead)
async def get_lab_template(
    template_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: LabTemplateService = Depends(get_lab_template_service),
) -> LabTemplate:
    return await service.get_template(current_user, template_id)


@router.get("/{template_id}/topology", response_model=TopologyRead)
async def get_lab_template_topology(
    template_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: LabTemplateService = Depends(get_lab_template_service),
) -> TopologyRead:
    template = await service.get_template(current_user, template_id)
    return TopologyParser().parse_containerlab_yaml(template.containerlab_yaml, actor=current_user)


@router.patch("/{template_id}", response_model=LabTemplateRead)
async def update_lab_template(
    template_id: uuid.UUID,
    payload: LabTemplateUpdate,
    current_user: User = Depends(get_current_user),
    service: LabTemplateService = Depends(get_lab_template_service),
) -> LabTemplate:
    return await service.update_template(current_user, template_id, payload)


@router.delete("/{template_id}", response_model=LabTemplateRead)
async def deactivate_lab_template(
    template_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: LabTemplateService = Depends(get_lab_template_service),
) -> LabTemplate:
    return await service.deactivate_template(current_user, template_id)


@router.post("/{template_id}/duplicate", response_model=LabTemplateRead, status_code=status.HTTP_201_CREATED)
async def duplicate_lab_template(
    template_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: LabTemplateService = Depends(get_lab_template_service),
) -> LabTemplate:
    return await service.duplicate_template(current_user, template_id)


@router.delete("/{template_id}/hard-delete", status_code=status.HTTP_204_NO_CONTENT)
async def hard_delete_lab_template(
    template_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: LabTemplateService = Depends(get_lab_template_service),
) -> None:
    await service.hard_delete_template(current_user, template_id)


@router.post("/{template_id}/validate", response_model=LabTemplateValidationResult)
async def validate_lab_template(
    template_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: LabTemplateService = Depends(get_lab_template_service),
) -> LabTemplateValidationResult:
    return await service.validate_template(current_user, template_id)
