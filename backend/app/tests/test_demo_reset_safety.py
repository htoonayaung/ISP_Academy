from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.lab_template import LabTemplate
from app.models.lab_instance import LabInstance, LabInstanceStatus
from app.models.ticket import Ticket
from app.models.user import User


async def test_demo_reset_requires_confirmation(
    client: AsyncClient,
    admin_token: str,
    auth_header,
) -> None:
    response = await client.post(
        "/api/v1/admin/demo/reset",
        headers=auth_header(admin_token),
        json={"confirm": "WRONG", "destroy_demo_labs": False},
    )

    assert response.status_code == 400


async def test_demo_reset_only_affects_demo_prefixed_data(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    admin_token: str,
    auth_header,
) -> None:
    await client.post(
        "/api/v1/admin/demo/setup",
        headers=auth_header(admin_token),
        json={"include_linux_demo": True, "activate_templates": True, "publish_tickets": True},
    )
    reset = await client.post(
        "/api/v1/admin/demo/reset",
        headers=auth_header(admin_token),
        json={"confirm": "RESET_DEMO_DATA", "destroy_demo_labs": False},
    )

    assert reset.status_code == 200
    async with session_factory() as session:
        demo_user = (await session.execute(select(User).where(User.username == "demo_student"))).scalar_one_or_none()
        admin_user = (await session.execute(select(User).where(User.username == "admin"))).scalar_one_or_none()
        template = (await session.execute(select(LabTemplate).where(LabTemplate.slug == "demo-basic-linux-lab"))).scalar_one_or_none()
        ticket = (await session.execute(select(Ticket).where(Ticket.slug == "demo-linux-verification-ticket"))).scalar_one_or_none()
        assert demo_user is None
        assert template is None
        assert ticket is None
        assert admin_user is not None


async def test_demo_reset_rejects_existing_demo_lab_without_destroy_confirmation(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    admin_token: str,
    auth_header,
) -> None:
    await client.post(
        "/api/v1/admin/demo/setup",
        headers=auth_header(admin_token),
        json={"include_linux_demo": True, "activate_templates": True, "publish_tickets": True},
    )
    async with session_factory() as session:
        template = (await session.execute(select(LabTemplate).where(LabTemplate.slug == "demo-basic-linux-lab"))).scalar_one()
        student = (await session.execute(select(User).where(User.username == "demo_student"))).scalar_one()
        session.add(
            LabInstance(
                template_id=template.id,
                owner_id=student.id,
                status=LabInstanceStatus.CREATED.value,
                lab_name="demo-reset-lab",
                lab_directory="/tmp/demo-reset-lab",
            )
        )
        await session.commit()

    response = await client.post(
        "/api/v1/admin/demo/reset",
        headers=auth_header(admin_token),
        json={"confirm": "RESET_DEMO_DATA", "destroy_demo_labs": False},
    )

    assert response.status_code == 409
