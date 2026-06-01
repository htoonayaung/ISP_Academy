from collections.abc import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.deps import get_db_session
from app.core.security import hash_password
from app.db.base import Base
from app.models.ai import AILabBuilderPreview  # noqa: F401
from app.models.lab_instance import LabEvent, LabInstance, LabNode  # noqa: F401
from app.models.lab_template import LabTemplate
from app.models.ticket import Ticket, TicketAttempt  # noqa: F401
from app.models.verification import VerificationResult, VerificationRule, VerificationRun  # noqa: F401
from app.main import app
from app.models.user import User, UserRole


VALID_LAB_YAML = """
name: basic-linux
topology:
  nodes:
    host1:
      kind: linux
      image: alpine:3.20
      cmd: sleep infinity
"""


@pytest_asyncio.fixture
async def session_factory() -> AsyncGenerator[async_sessionmaker[AsyncSession], None]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    yield factory
    await engine.dispose()


@pytest_asyncio.fixture
async def client(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db_session() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_get_db_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def seeded_users(session_factory: async_sessionmaker[AsyncSession]) -> dict[str, User]:
    async with session_factory() as session:
        users = {
            "admin": User(
                email="admin@example.com",
                username="admin",
                hashed_password=hash_password("AdminPassword123!"),
                full_name="Admin User",
                role=UserRole.ADMIN,
                is_active=True,
            ),
            "instructor": User(
                email="instructor@example.com",
                username="instructor",
                hashed_password=hash_password("InstructorPassword123!"),
                full_name="Instructor User",
                role=UserRole.INSTRUCTOR,
                is_active=True,
            ),
            "instructor2": User(
                email="instructor2@example.com",
                username="instructor2",
                hashed_password=hash_password("InstructorPassword123!"),
                full_name="Second Instructor",
                role=UserRole.INSTRUCTOR,
                is_active=True,
            ),
            "student": User(
                email="student@example.com",
                username="student",
                hashed_password=hash_password("StudentPassword123!"),
                full_name="Student User",
                role=UserRole.STUDENT,
                is_active=True,
            ),
            "inactive": User(
                email="inactive@example.com",
                username="inactive",
                hashed_password=hash_password("InactivePassword123!"),
                full_name="Inactive User",
                role=UserRole.STUDENT,
                is_active=False,
            ),
        }
        session.add_all(users.values())
        await session.commit()
        for user in users.values():
            await session.refresh(user)
        return users


@pytest_asyncio.fixture
async def admin_token(client: AsyncClient, seeded_users: dict[str, User]) -> str:
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "AdminPassword123!"},
    )
    return response.json()["access_token"]


@pytest_asyncio.fixture
async def instructor_token(client: AsyncClient, seeded_users: dict[str, User]) -> str:
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "instructor", "password": "InstructorPassword123!"},
    )
    return response.json()["access_token"]


@pytest_asyncio.fixture
async def student_token(client: AsyncClient, seeded_users: dict[str, User]) -> str:
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "student", "password": "StudentPassword123!"},
    )
    return response.json()["access_token"]


@pytest.fixture
def auth_header() -> Generator:
    def build(token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"}

    yield build


@pytest_asyncio.fixture
async def active_template(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_users: dict[str, User],
) -> LabTemplate:
    async with session_factory() as session:
        template = LabTemplate(
            name="Active Lab",
            slug="active-lab",
            description="Active lab",
            category="Linux",
            difficulty="Easy",
            containerlab_yaml=VALID_LAB_YAML,
            estimated_cpu=1,
            estimated_memory_mb=128,
            estimated_duration_minutes=30,
            is_active=True,
            created_by=seeded_users["admin"].id,
        )
        session.add(template)
        await session.commit()
        await session.refresh(template)
        return template


@pytest_asyncio.fixture
async def inactive_template(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_users: dict[str, User],
) -> LabTemplate:
    async with session_factory() as session:
        template = LabTemplate(
            name="Inactive Lab",
            slug="inactive-lab",
            description="Inactive lab",
            category="Linux",
            difficulty="Easy",
            containerlab_yaml=VALID_LAB_YAML,
            estimated_cpu=1,
            estimated_memory_mb=128,
            estimated_duration_minutes=30,
            is_active=False,
            created_by=seeded_users["admin"].id,
        )
        session.add(template)
        await session.commit()
        await session.refresh(template)
        return template
