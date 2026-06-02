import uuid
from datetime import UTC, datetime, time
from typing import Any

from fastapi import HTTPException, status

from app.adapters.ai_provider import AIProvider, AIProviderConfig, AIProviderConfigurationError, AIProviderResponseError
from app.lab_runtime.name_sanitizer import slugify
from app.models.ai import (
    AILabBuilderPreview,
    AILabBuilderPreviewStatus,
    AILabBuilderValidationStatus,
)
from app.models.lab_template import LabTemplate
from app.models.user import User, UserRole
from app.repositories.ai import AILabBuilderPreviewRepository
from app.repositories.lab_templates import LabTemplateRepository
from app.services.ai_lab_generators import (
    ContainerlabYamlGenerator,
    FRRConfigGenerator,
    LabPreviewExplanationGenerator,
    VerificationRulePreviewGenerator,
)
from app.services.ai_lab_plan_validator import LabPlanValidator


class AILabBuilderService:
    def __init__(
        self,
        repository: AILabBuilderPreviewRepository,
        template_repository: LabTemplateRepository,
        provider: AIProvider,
        provider_config: AIProviderConfig,
        enabled: bool,
        validator: LabPlanValidator | None = None,
        yaml_generator: ContainerlabYamlGenerator | None = None,
        config_generator: FRRConfigGenerator | None = None,
        rule_generator: VerificationRulePreviewGenerator | None = None,
        explanation_generator: LabPreviewExplanationGenerator | None = None,
    ) -> None:
        self.repository = repository
        self.template_repository = template_repository
        self.provider = provider
        self.provider_config = provider_config
        self.enabled = enabled
        self.validator = validator or LabPlanValidator()
        self.yaml_generator = yaml_generator or ContainerlabYamlGenerator()
        self.config_generator = config_generator or FRRConfigGenerator()
        self.rule_generator = rule_generator or VerificationRulePreviewGenerator()
        self.explanation_generator = explanation_generator or LabPreviewExplanationGenerator()

    async def create_preview(
        self,
        actor: User,
        prompt: str,
        confirm_real_provider_usage: bool = False,
    ) -> AILabBuilderPreview:
        self._require_admin_or_instructor(actor)
        self._require_enabled()
        await self._enforce_real_provider_guards(actor, confirm_real_provider_usage)
        try:
            raw_plan = await self.provider.generate_lab_plan(prompt)
        except AIProviderConfigurationError as exc:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
        except AIProviderResponseError as exc:
            return await self._store_invalid_preview(actor, prompt, [str(exc)])
        validation = self.validator.validate_raw(raw_plan)
        generated_yaml = ""
        configs: list[dict[str, Any]] = []
        rules: list[dict[str, Any]] = []
        errors = list(validation.errors)

        if validation.lab_plan is not None:
            generated_yaml = self.yaml_generator.generate(validation.lab_plan)
            configs = self.config_generator.generate(validation.lab_plan)
            rules = self.rule_generator.generate(validation.lab_plan)
            errors.extend(self.validator.validate_generated_yaml(generated_yaml))

        is_valid = not errors and validation.lab_plan is not None
        if validation.lab_plan is not None:
            raw_plan = validation.lab_plan.model_dump()
            raw_plan["explanation"] = self.explanation_generator.generate(validation.lab_plan)

        preview = AILabBuilderPreview(
            requested_by=actor.id,
            prompt=prompt,
            lab_plan_json=raw_plan,
            generated_containerlab_yaml=generated_yaml,
            generated_configs=configs,
            generated_verification_rules=rules,
            validation_status=(
                AILabBuilderValidationStatus.PASSED.value
                if is_valid
                else AILabBuilderValidationStatus.FAILED.value
            ),
            validation_errors=errors,
            status=(
                AILabBuilderPreviewStatus.VALID.value
                if is_valid
                else AILabBuilderPreviewStatus.INVALID.value
            ),
        )
        created = await self.repository.create(preview)
        await self.repository.commit()
        await self.repository.refresh(created)
        return created

    async def provider_status(self, actor: User) -> dict[str, Any]:
        if actor.role != UserRole.ADMIN:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
        return {
            "enabled": self.provider_config.enabled,
            "provider": self.provider_config.provider,
            "model": self.provider_config.model,
            "base_url_host_only": self.provider_config.base_url_host_only,
            "has_api_key": self.provider_config.has_api_key,
            "provider_test_enabled": self.provider_config.provider_test_enabled,
            "daily_preview_limit_per_user": self.provider_config.daily_preview_limit_per_user,
            "real_provider_confirmation_required": (
                self.provider_config.is_real_provider
                and self.provider_config.real_provider_confirmation_required
            ),
        }

    async def list_previews(self, actor: User) -> list[AILabBuilderPreview]:
        self._require_admin_or_instructor(actor)
        if actor.role == UserRole.ADMIN:
            return await self.repository.list_all()
        return await self.repository.list_by_requester(actor.id)

    async def get_preview(self, actor: User, preview_id: uuid.UUID) -> AILabBuilderPreview:
        preview = await self.repository.get_by_id(preview_id)
        if preview is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI preview not found")
        self._require_owner_or_admin(actor, preview)
        return preview

    async def approve_preview(self, actor: User, preview_id: uuid.UUID) -> AILabBuilderPreview:
        preview = await self.get_preview(actor, preview_id)
        if preview.status == AILabBuilderPreviewStatus.APPROVED.value:
            return preview
        if preview.status == AILabBuilderPreviewStatus.REJECTED.value:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Rejected preview cannot be approved")

        validation = self.validator.validate_raw(preview.lab_plan_json)
        if validation.lab_plan is None:
            preview.validation_status = AILabBuilderValidationStatus.FAILED.value
            preview.validation_errors = validation.errors
            preview.status = AILabBuilderPreviewStatus.INVALID.value
            await self.repository.commit()
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=validation.errors)

        generated_yaml = self.yaml_generator.generate(validation.lab_plan)
        errors = validation.errors + self.validator.validate_generated_yaml(generated_yaml)
        if errors:
            preview.generated_containerlab_yaml = generated_yaml
            preview.validation_status = AILabBuilderValidationStatus.FAILED.value
            preview.validation_errors = errors
            preview.status = AILabBuilderPreviewStatus.INVALID.value
            await self.repository.commit()
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=errors)

        template = LabTemplate(
            name=validation.lab_plan.title,
            slug=await self._unique_template_slug(validation.lab_plan.title),
            description=validation.lab_plan.description,
            category=validation.lab_plan.category,
            difficulty=validation.lab_plan.difficulty,
            containerlab_yaml=generated_yaml,
            default_startup_config="\n\n".join(
                config.get("content", "") for config in self.config_generator.generate(validation.lab_plan)
            )
            or None,
            estimated_cpu=validation.lab_plan.estimated_cpu,
            estimated_memory_mb=validation.lab_plan.estimated_memory_mb,
            estimated_duration_minutes=validation.lab_plan.estimated_duration_minutes,
            is_active=False,
            created_by=actor.id,
        )
        created_template = await self.template_repository.create(template)
        preview.generated_containerlab_yaml = generated_yaml
        preview.generated_configs = self.config_generator.generate(validation.lab_plan)
        preview.generated_verification_rules = self.rule_generator.generate(validation.lab_plan)
        preview.validation_status = AILabBuilderValidationStatus.PASSED.value
        preview.validation_errors = []
        preview.status = AILabBuilderPreviewStatus.APPROVED.value
        preview.approved_at = datetime.now(UTC)
        preview.approved_by = actor.id
        preview.created_lab_template_id = created_template.id
        await self.repository.commit()
        await self.repository.refresh(preview)
        return preview

    async def reject_preview(self, actor: User, preview_id: uuid.UUID) -> AILabBuilderPreview:
        preview = await self.get_preview(actor, preview_id)
        if preview.status == AILabBuilderPreviewStatus.APPROVED.value:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Approved preview cannot be rejected")
        preview.status = AILabBuilderPreviewStatus.REJECTED.value
        await self.repository.commit()
        await self.repository.refresh(preview)
        return preview

    async def delete_preview(self, actor: User, preview_id: uuid.UUID) -> None:
        preview = await self.get_preview(actor, preview_id)
        if actor.role != UserRole.ADMIN and preview.status == AILabBuilderPreviewStatus.APPROVED.value:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Approved preview cannot be deleted by instructor")
        await self.repository.delete(preview)
        await self.repository.commit()

    def _require_enabled(self) -> None:
        if not self.enabled:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="AI Lab Builder is disabled")

    async def _enforce_real_provider_guards(self, actor: User, confirm_real_provider_usage: bool) -> None:
        if not self.provider_config.is_real_provider:
            return
        if self.provider_config.real_provider_confirmation_required and not confirm_real_provider_usage:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Real AI provider usage requires explicit confirmation.",
            )
        today = datetime.combine(datetime.now(UTC).date(), time.min, tzinfo=UTC)
        preview_count = await self.repository.count_by_requester_since(actor.id, today)
        if preview_count >= self.provider_config.daily_preview_limit_per_user:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Daily AI preview limit exceeded for this user.",
            )

    async def _store_invalid_preview(self, actor: User, prompt: str, errors: list[str]) -> AILabBuilderPreview:
        preview = AILabBuilderPreview(
            requested_by=actor.id,
            prompt=prompt,
            lab_plan_json={"error": "AI provider response could not be parsed"},
            generated_containerlab_yaml="",
            generated_configs=[],
            generated_verification_rules=[],
            validation_status=AILabBuilderValidationStatus.FAILED.value,
            validation_errors=errors,
            status=AILabBuilderPreviewStatus.INVALID.value,
        )
        created = await self.repository.create(preview)
        await self.repository.commit()
        await self.repository.refresh(created)
        return created

    @staticmethod
    def _require_admin_or_instructor(actor: User) -> None:
        if actor.role not in {UserRole.ADMIN, UserRole.INSTRUCTOR}:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    @staticmethod
    def _require_owner_or_admin(actor: User, preview: AILabBuilderPreview) -> None:
        if actor.role == UserRole.ADMIN:
            return
        if actor.role == UserRole.INSTRUCTOR and preview.requested_by == actor.id:
            return
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    async def _unique_template_slug(self, name: str) -> str:
        base_slug = slugify(name)
        candidate = base_slug
        suffix = 2
        while await self.template_repository.get_by_slug(candidate) is not None:
            candidate = f"{base_slug}-{suffix}"
            suffix += 1
        return candidate
