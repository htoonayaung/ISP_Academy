from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.adapters.ai_provider import MockAIProvider
from app.api.v1.ai_lab_builder import get_ai_lab_builder_service
from app.main import app
from app.models.lab_instance import LabInstance
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
                enabled=True,
            )

    app.dependency_overrides[get_ai_lab_builder_service] = override_service


async def test_approval_creates_lab_template_without_lab_instance(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    admin_token: str,
    auth_header,
) -> None:
    enable_mock_ai(session_factory)
    preview_response = await client.post(
        "/api/v1/ai-lab-builder/preview",
        headers=auth_header(admin_token),
        json={"prompt": "Create a basic Linux lab with one Alpine host named host1."},
    )
    preview_id = preview_response.json()["id"]

    approval_response = await client.post(
        f"/api/v1/ai-lab-builder/previews/{preview_id}/approve",
        headers=auth_header(admin_token),
    )

    assert approval_response.status_code == 200
    payload = approval_response.json()
    assert payload["created_lab_template_id"]
    assert payload["preview"]["status"] == "APPROVED"

    templates_response = await client.get(
        f"/api/v1/lab-templates/{payload['created_lab_template_id']}",
        headers=auth_header(admin_token),
    )
    assert templates_response.status_code == 200
    assert templates_response.json()["is_active"] is False

    async with session_factory() as session:
        result = await session.execute(select(LabInstance))
        assert list(result.scalars().all()) == []


async def test_instructor_can_approve_own_preview(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    instructor_token: str,
    auth_header,
) -> None:
    enable_mock_ai(session_factory)
    preview_response = await client.post(
        "/api/v1/ai-lab-builder/preview",
        headers=auth_header(instructor_token),
        json={"prompt": "Create a basic Linux lab with one Alpine host named host1."},
    )

    approval_response = await client.post(
        f"/api/v1/ai-lab-builder/previews/{preview_response.json()['id']}/approve",
        headers=auth_header(instructor_token),
    )

    assert approval_response.status_code == 200
