from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.lab_instance import LabInstance
from app.models.lab_template import LabTemplate
from app.models.ticket import Ticket, TicketStatus
from app.models.user import User
from app.models.verification import VerificationRule


async def test_admin_can_get_demo_status(
    client: AsyncClient,
    admin_token: str,
    auth_header,
) -> None:
    response = await client.get("/api/v1/admin/demo/status", headers=auth_header(admin_token))

    assert response.status_code == 200
    payload = response.json()
    assert payload["demo_ready"] is False
    assert payload["safe_to_run_setup"] is True


async def test_admin_can_run_demo_setup(
    client: AsyncClient,
    admin_token: str,
    auth_header,
) -> None:
    response = await client.post(
        "/api/v1/admin/demo/setup",
        headers=auth_header(admin_token),
        json={
            "include_linux_demo": True,
            "include_frr_demo": False,
            "activate_templates": True,
            "publish_tickets": True,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert any(account["username"] == "demo_student" for account in payload["demo_accounts"])
    assert "Start attempt." in payload["next_steps"]


async def test_demo_setup_is_idempotent(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    admin_token: str,
    auth_header,
) -> None:
    payload = {
        "include_linux_demo": True,
        "include_frr_demo": False,
        "activate_templates": True,
        "publish_tickets": True,
    }
    first = await client.post("/api/v1/admin/demo/setup", headers=auth_header(admin_token), json=payload)
    second = await client.post("/api/v1/admin/demo/setup", headers=auth_header(admin_token), json=payload)

    assert first.status_code == 200
    assert second.status_code == 200
    assert len(second.json()["created"]) == 0
    async with session_factory() as session:
        users = await session.execute(select(User).where(User.username.in_(["demo_instructor", "demo_student"])))
        templates = await session.execute(select(LabTemplate).where(LabTemplate.slug == "demo-basic-linux-lab"))
        tickets = await session.execute(select(Ticket).where(Ticket.slug == "demo-linux-verification-ticket"))
        assert len(list(users.scalars().all())) == 2
        assert len(list(templates.scalars().all())) == 1
        assert len(list(tickets.scalars().all())) == 1


async def test_demo_setup_creates_content_without_lab_instance(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    admin_token: str,
    auth_header,
) -> None:
    response = await client.post(
        "/api/v1/admin/demo/setup",
        headers=auth_header(admin_token),
        json={"include_linux_demo": True, "activate_templates": True, "publish_tickets": True},
    )

    assert response.status_code == 200
    async with session_factory() as session:
        template = (await session.execute(select(LabTemplate).where(LabTemplate.slug == "demo-basic-linux-lab"))).scalar_one()
        ticket = (await session.execute(select(Ticket).where(Ticket.slug == "demo-linux-verification-ticket"))).scalar_one()
        rule = (await session.execute(select(VerificationRule).where(VerificationRule.ticket_id == ticket.id))).scalar_one()
        labs = (await session.execute(select(LabInstance))).scalars().all()
        assert template.is_active is True
        assert ticket.status == TicketStatus.PUBLISHED.value
        assert rule.target_node == "host1"
        assert rule.command == "uname"
        assert list(labs) == []
