import uuid

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.lab_runtime.name_sanitizer import slugify
from app.lab_runtime.yaml_validator import ContainerlabYamlValidator
from app.models.lab_template import LabTemplate
from app.models.user import User, UserRole
from app.repositories.lab_templates import LabTemplateRepository
from app.schemas.lab_template import (
    LabTemplateCreate,
    LabTemplateUpdate,
    LabTemplateValidationResult,
)


class LabTemplateService:
    def __init__(
        self,
        repository: LabTemplateRepository,
        validator: ContainerlabYamlValidator | None = None,
    ) -> None:
        self.repository = repository
        self.validator = validator or ContainerlabYamlValidator()

    async def create_template(self, actor: User, data: LabTemplateCreate) -> LabTemplate:
        self._require_admin_or_instructor(actor)
        validation = self.validate_yaml(data.containerlab_yaml)
        if not validation.is_valid:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=validation.errors)

        template = LabTemplate(
            name=data.name,
            slug=await self._unique_slug(data.name),
            description=data.description,
            category=data.category.value,
            difficulty=data.difficulty.value,
            containerlab_yaml=data.containerlab_yaml,
            default_startup_config=data.default_startup_config,
            estimated_cpu=data.estimated_cpu,
            estimated_memory_mb=data.estimated_memory_mb,
            estimated_duration_minutes=data.estimated_duration_minutes,
            is_active=data.is_active,
            created_by=actor.id,
        )
        try:
            created = await self.repository.create(template)
            await self.repository.commit()
            await self.repository.refresh(created)
            return created
        except IntegrityError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Lab template slug already exists",
            ) from exc

    async def list_templates(self, actor: User) -> list[LabTemplate]:
        if actor.role == UserRole.ADMIN:
            return await self.repository.list_all()
        if actor.role == UserRole.INSTRUCTOR:
            return await self.repository.list_visible_to_instructor(actor.id)
        return await self.repository.list_active()

    async def get_template(self, actor: User, template_id: uuid.UUID) -> LabTemplate:
        template = await self.repository.get_by_id(template_id)
        if template is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lab template not found")

        if actor.role == UserRole.ADMIN:
            return template
        if actor.role == UserRole.INSTRUCTOR and (template.created_by == actor.id or template.is_active):
            return template
        if actor.role == UserRole.STUDENT and template.is_active:
            return template
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    async def update_template(
        self,
        actor: User,
        template_id: uuid.UUID,
        data: LabTemplateUpdate,
    ) -> LabTemplate:
        template = await self.get_template(actor, template_id)
        self._require_owner_or_admin(actor, template)

        if data.containerlab_yaml is not None:
            validation = self.validate_yaml(data.containerlab_yaml)
            if not validation.is_valid:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=validation.errors)
            template.containerlab_yaml = data.containerlab_yaml

        if data.name is not None:
            template.name = data.name
            template.slug = await self._unique_slug(data.name, exclude_id=template.id)
        if data.description is not None:
            template.description = data.description
        if data.category is not None:
            template.category = data.category.value
        if data.difficulty is not None:
            template.difficulty = data.difficulty.value
        if data.default_startup_config is not None:
            template.default_startup_config = data.default_startup_config
        if data.estimated_cpu is not None:
            template.estimated_cpu = data.estimated_cpu
        if data.estimated_memory_mb is not None:
            template.estimated_memory_mb = data.estimated_memory_mb
        if data.estimated_duration_minutes is not None:
            template.estimated_duration_minutes = data.estimated_duration_minutes
        if data.is_active is not None:
            template.is_active = data.is_active

        try:
            await self.repository.commit()
            await self.repository.refresh(template)
            return template
        except IntegrityError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Lab template slug already exists",
            ) from exc

    async def deactivate_template(self, actor: User, template_id: uuid.UUID) -> LabTemplate:
        template = await self.get_template(actor, template_id)
        self._require_owner_or_admin(actor, template)
        template.is_active = False
        await self.repository.commit()
        await self.repository.refresh(template)
        return template

    async def validate_template(
        self,
        actor: User,
        template_id: uuid.UUID,
    ) -> LabTemplateValidationResult:
        template = await self.get_template(actor, template_id)
        self._require_owner_or_admin(actor, template)
        return self.validate_yaml(template.containerlab_yaml)

    def validate_yaml(self, raw_yaml: str) -> LabTemplateValidationResult:
        result = self.validator.validate(raw_yaml)
        return LabTemplateValidationResult(
            is_valid=result.is_valid,
            errors=result.errors,
            warnings=result.warnings,
        )

    async def _unique_slug(self, name: str, exclude_id: uuid.UUID | None = None) -> str:
        base_slug = slugify(name)
        candidate = base_slug
        suffix = 2
        while True:
            existing = await self.repository.get_by_slug(candidate)
            if existing is None or existing.id == exclude_id:
                return candidate
            candidate = f"{base_slug}-{suffix}"
            suffix += 1

    @staticmethod
    def _require_admin_or_instructor(actor: User) -> None:
        if actor.role not in {UserRole.ADMIN, UserRole.INSTRUCTOR}:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    @staticmethod
    def _require_owner_or_admin(actor: User, template: LabTemplate) -> None:
        if actor.role == UserRole.ADMIN:
            return
        if actor.role == UserRole.INSTRUCTOR and template.created_by == actor.id:
            return
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

