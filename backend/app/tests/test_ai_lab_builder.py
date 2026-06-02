from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.adapters.ai_provider import MockAIProvider, build_ai_provider_config
from app.api.v1.ai_lab_builder import get_ai_lab_builder_service
from app.core.config import get_settings
from app.main import app
from app.repositories.ai import AILabBuilderPreviewRepository
from app.repositories.lab_templates import LabTemplateRepository
from app.services.ai_lab_builder_service import AILabBuilderService


def enable_mock_ai(session_factory: async_sessionmaker[AsyncSession]) -> None:
    async def override_service():
        async with session_factory() as session:
            yield AILabBuilderService(
                repository=AILabBuilderPreviewRepository(session),
                template_repository=LabTemplateRepository(session),
                provider=MockAIProvider(),
                provider_config=build_ai_provider_config(get_settings()),
                enabled=True,
            )

    app.dependency_overrides[get_ai_lab_builder_service] = override_service


async def test_ai_disabled_returns_clear_response(
    client: AsyncClient,
    admin_token: str,
    auth_header,
) -> None:
    response = await client.post(
        "/api/v1/ai-lab-builder/preview",
        headers=auth_header(admin_token),
        json={"prompt": "Create a basic Linux lab with one Alpine host named host1."},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "AI Lab Builder is disabled"


async def test_admin_can_create_preview(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    admin_token: str,
    auth_header,
) -> None:
    enable_mock_ai(session_factory)
    response = await client.post(
        "/api/v1/ai-lab-builder/preview",
        headers=auth_header(admin_token),
        json={"prompt": "Create a basic Linux lab with one Alpine host named host1."},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "VALID"
    assert payload["validation_status"] == "PASSED"
    assert "topology" in payload["generated_containerlab_yaml"]
    assert payload["generated_verification_rules"][0]["target_node"] == "host1"


async def test_instructor_can_create_preview(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    instructor_token: str,
    auth_header,
) -> None:
    enable_mock_ai(session_factory)
    response = await client.post(
        "/api/v1/ai-lab-builder/preview",
        headers=auth_header(instructor_token),
        json={"prompt": "Create a two-router FRR eBGP lab."},
    )

    assert response.status_code == 201
    assert response.json()["lab_plan_json"]["category"] == "BGP"


async def test_student_cannot_create_preview(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    student_token: str,
    auth_header,
) -> None:
    enable_mock_ai(session_factory)
    response = await client.post(
        "/api/v1/ai-lab-builder/preview",
        headers=auth_header(student_token),
        json={"prompt": "Create a basic Linux lab with one Alpine host named host1."},
    )

    assert response.status_code == 403
