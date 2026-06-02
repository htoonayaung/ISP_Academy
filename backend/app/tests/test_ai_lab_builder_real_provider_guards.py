from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.adapters.ai_provider import (
    AIProvider,
    AIProviderConfig,
    AIProviderResponseError,
    MockAIProvider,
    OpenAICompatibleProvider,
)
from app.api.v1.ai_lab_builder import get_ai_lab_builder_service
from app.main import app
from app.repositories.ai import AILabBuilderPreviewRepository
from app.repositories.lab_templates import LabTemplateRepository
from app.services.ai_lab_builder_service import AILabBuilderService


def enable_guarded_real_provider(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    daily_limit: int = 20,
    has_api_key: bool = True,
) -> None:
    async def override_service():
        async with session_factory() as session:
            yield AILabBuilderService(
                repository=AILabBuilderPreviewRepository(session),
                template_repository=LabTemplateRepository(session),
                provider=MockAIProvider(),
                provider_config=AIProviderConfig(
                    enabled=True,
                    provider="groq",
                    model="llama-3.3-70b-versatile",
                    base_url="https://api.groq.com/openai/v1",
                    api_key="test-key" if has_api_key else "",
                    request_timeout_seconds=5,
                    max_tokens=100,
                    provider_test_enabled=False,
                    daily_preview_limit_per_user=daily_limit,
                    real_provider_confirmation_required=True,
                ),
                enabled=True,
            )

    app.dependency_overrides[get_ai_lab_builder_service] = override_service


def enable_real_provider_missing_key(session_factory: async_sessionmaker[AsyncSession]) -> None:
    async def override_service():
        config = AIProviderConfig(
            enabled=True,
            provider="groq",
            model="llama-3.3-70b-versatile",
            base_url="https://api.groq.com/openai/v1",
            api_key="",
            request_timeout_seconds=5,
            max_tokens=100,
            provider_test_enabled=False,
            daily_preview_limit_per_user=20,
            real_provider_confirmation_required=False,
        )
        async with session_factory() as session:
            yield AILabBuilderService(
                repository=AILabBuilderPreviewRepository(session),
                template_repository=LabTemplateRepository(session),
                provider=OpenAICompatibleProvider(config),
                provider_config=config,
                enabled=True,
            )

    app.dependency_overrides[get_ai_lab_builder_service] = override_service


class InvalidJsonProvider(AIProvider):
    async def generate_lab_plan(self, prompt: str) -> dict:
        raise AIProviderResponseError("AI provider returned invalid JSON")


def enable_invalid_json_provider(session_factory: async_sessionmaker[AsyncSession]) -> None:
    async def override_service():
        async with session_factory() as session:
            yield AILabBuilderService(
                repository=AILabBuilderPreviewRepository(session),
                template_repository=LabTemplateRepository(session),
                provider=InvalidJsonProvider(),
                provider_config=AIProviderConfig(
                    enabled=True,
                    provider="mock",
                    model="mock",
                    base_url=None,
                    api_key=None,
                    request_timeout_seconds=5,
                    max_tokens=100,
                    provider_test_enabled=False,
                    daily_preview_limit_per_user=20,
                    real_provider_confirmation_required=True,
                ),
                enabled=True,
            )

    app.dependency_overrides[get_ai_lab_builder_service] = override_service


async def test_provider_status_hides_api_key(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    admin_token: str,
    auth_header,
) -> None:
    enable_guarded_real_provider(session_factory)

    response = await client.get(
        "/api/v1/ai-lab-builder/provider/status",
        headers=auth_header(admin_token),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"] == "groq"
    assert payload["base_url_host_only"] == "api.groq.com"
    assert payload["has_api_key"] is True
    assert "test-key" not in str(payload)


async def test_student_cannot_access_provider_status(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    student_token: str,
    auth_header,
) -> None:
    enable_guarded_real_provider(session_factory)

    response = await client.get(
        "/api/v1/ai-lab-builder/provider/status",
        headers=auth_header(student_token),
    )

    assert response.status_code == 403


async def test_real_provider_preview_requires_confirmation(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    admin_token: str,
    auth_header,
) -> None:
    enable_guarded_real_provider(session_factory)

    response = await client.post(
        "/api/v1/ai-lab-builder/preview",
        headers=auth_header(admin_token),
        json={"prompt": "Create a basic Linux lab with one Alpine host named host1."},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Real AI provider usage requires explicit confirmation."


async def test_real_provider_preview_accepts_confirmation(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    admin_token: str,
    auth_header,
) -> None:
    enable_guarded_real_provider(session_factory)

    response = await client.post(
        "/api/v1/ai-lab-builder/preview",
        headers=auth_header(admin_token),
        json={
            "prompt": "Create a basic Linux lab with one Alpine host named host1.",
            "confirm_real_provider_usage": True,
        },
    )

    assert response.status_code == 201
    assert response.json()["validation_status"] == "PASSED"


async def test_real_provider_without_api_key_returns_config_error(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    admin_token: str,
    auth_header,
) -> None:
    enable_real_provider_missing_key(session_factory)

    response = await client.post(
        "/api/v1/ai-lab-builder/preview",
        headers=auth_header(admin_token),
        json={
            "prompt": "Create a basic Linux lab with one Alpine host named host1.",
            "confirm_real_provider_usage": True,
        },
    )

    assert response.status_code == 503
    assert "AI_API_KEY" in response.json()["detail"]


async def test_invalid_provider_json_creates_invalid_preview(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    admin_token: str,
    auth_header,
) -> None:
    enable_invalid_json_provider(session_factory)

    response = await client.post(
        "/api/v1/ai-lab-builder/preview",
        headers=auth_header(admin_token),
        json={"prompt": "Create a basic Linux lab with one Alpine host named host1."},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "INVALID"
    assert payload["validation_status"] == "FAILED"
    assert payload["validation_errors"] == ["AI provider returned invalid JSON"]


async def test_real_provider_daily_limit_is_enforced(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    admin_token: str,
    auth_header,
) -> None:
    enable_guarded_real_provider(session_factory, daily_limit=1)
    payload = {
        "prompt": "Create a basic Linux lab with one Alpine host named host1.",
        "confirm_real_provider_usage": True,
    }

    first = await client.post(
        "/api/v1/ai-lab-builder/preview",
        headers=auth_header(admin_token),
        json=payload,
    )
    second = await client.post(
        "/api/v1/ai-lab-builder/preview",
        headers=auth_header(admin_token),
        json=payload,
    )

    assert first.status_code == 201
    assert second.status_code == 429
