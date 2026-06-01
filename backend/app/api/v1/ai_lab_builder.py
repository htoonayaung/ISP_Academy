import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.ai_provider import build_ai_provider
from app.api.deps import get_db_session
from app.core.config import get_settings
from app.core.permissions import get_current_user
from app.models.ai import AILabBuilderPreview
from app.models.user import User
from app.repositories.ai import AILabBuilderPreviewRepository
from app.repositories.lab_templates import LabTemplateRepository
from app.schemas.ai import AILabBuilderApprovalRead, AILabBuilderPreviewCreate, AILabBuilderPreviewRead
from app.services.ai_lab_builder_service import AILabBuilderService

router = APIRouter(tags=["ai-lab-builder"])


def get_ai_lab_builder_service(session: AsyncSession = Depends(get_db_session)) -> AILabBuilderService:
    settings = get_settings()
    return AILabBuilderService(
        repository=AILabBuilderPreviewRepository(session),
        template_repository=LabTemplateRepository(session),
        provider=build_ai_provider(settings),
        enabled=settings.ai_lab_builder_enabled,
    )


@router.post("/preview", response_model=AILabBuilderPreviewRead, status_code=status.HTTP_201_CREATED)
async def create_ai_lab_preview(
    payload: AILabBuilderPreviewCreate,
    current_user: User = Depends(get_current_user),
    service: AILabBuilderService = Depends(get_ai_lab_builder_service),
) -> AILabBuilderPreview:
    return await service.create_preview(current_user, payload.prompt)


@router.get("/previews", response_model=list[AILabBuilderPreviewRead])
async def list_ai_lab_previews(
    current_user: User = Depends(get_current_user),
    service: AILabBuilderService = Depends(get_ai_lab_builder_service),
) -> list[AILabBuilderPreview]:
    return await service.list_previews(current_user)


@router.get("/previews/{preview_id}", response_model=AILabBuilderPreviewRead)
async def get_ai_lab_preview(
    preview_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: AILabBuilderService = Depends(get_ai_lab_builder_service),
) -> AILabBuilderPreview:
    return await service.get_preview(current_user, preview_id)


@router.post("/previews/{preview_id}/approve", response_model=AILabBuilderApprovalRead)
async def approve_ai_lab_preview(
    preview_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: AILabBuilderService = Depends(get_ai_lab_builder_service),
) -> AILabBuilderApprovalRead:
    preview = await service.approve_preview(current_user, preview_id)
    if preview.created_lab_template_id is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Approval did not create lab template")
    return AILabBuilderApprovalRead(
        preview=AILabBuilderPreviewRead.model_validate(preview),
        created_lab_template_id=preview.created_lab_template_id,
    )


@router.post("/previews/{preview_id}/reject", response_model=AILabBuilderPreviewRead)
async def reject_ai_lab_preview(
    preview_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: AILabBuilderService = Depends(get_ai_lab_builder_service),
) -> AILabBuilderPreview:
    return await service.reject_preview(current_user, preview_id)


@router.delete("/previews/{preview_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ai_lab_preview(
    preview_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: AILabBuilderService = Depends(get_ai_lab_builder_service),
) -> Response:
    await service.delete_preview(current_user, preview_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
