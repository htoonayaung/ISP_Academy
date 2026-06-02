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


async def create_preview(client: AsyncClient, token: str, auth_header) -> str:
    response = await client.post(
        "/api/v1/ai-lab-builder/preview",
        headers=auth_header(token),
        json={"prompt": "Create a basic Linux lab with one Alpine host named host1."},
    )
    return response.json()["id"]


async def test_admin_and_owner_can_view_previews(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    admin_token: str,
    instructor_token: str,
    auth_header,
) -> None:
    enable_mock_ai(session_factory)
    await create_preview(client, instructor_token, auth_header)

    instructor_response = await client.get(
        "/api/v1/ai-lab-builder/previews",
        headers=auth_header(instructor_token),
    )
    admin_response = await client.get(
        "/api/v1/ai-lab-builder/previews",
        headers=auth_header(admin_token),
    )

    assert instructor_response.status_code == 200
    assert len(instructor_response.json()) == 1
    assert admin_response.status_code == 200
    assert len(admin_response.json()) == 1


async def test_student_cannot_view_previews(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    student_token: str,
    auth_header,
) -> None:
    enable_mock_ai(session_factory)
    response = await client.get(
        "/api/v1/ai-lab-builder/previews",
        headers=auth_header(student_token),
    )

    assert response.status_code == 403


async def test_instructor_cannot_approve_other_instructor_preview(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    instructor_token: str,
    auth_header,
) -> None:
    enable_mock_ai(session_factory)
    preview_id = await create_preview(client, instructor_token, auth_header)

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"username": "instructor2", "password": "InstructorPassword123!"},
    )
    instructor2_token = login_response.json()["access_token"]
    response = await client.post(
        f"/api/v1/ai-lab-builder/previews/{preview_id}/approve",
        headers=auth_header(instructor2_token),
    )

    assert response.status_code == 403
