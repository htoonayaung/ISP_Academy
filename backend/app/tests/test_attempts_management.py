from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.lab_instance import LabInstance
from app.models.lab_template import LabTemplate
from app.models.ticket import Ticket, TicketAttempt, TicketStatus
from app.models.user import User


async def _create_attempt(
    session_factory: async_sessionmaker[AsyncSession],
    template: LabTemplate,
    instructor: User,
    student: User,
    slug_suffix: str,
) -> TicketAttempt:
    async with session_factory() as session:
        ticket = Ticket(
            lab_template_id=template.id,
            title=f"Attempt Ticket {slug_suffix}",
            slug=f"attempt-ticket-{slug_suffix}",
            description="Ticket for attempt management.",
            student_instructions="Start the lab and run verification.",
            hints=None,
            hidden_solution="Instructor only",
            status=TicketStatus.PUBLISHED.value,
            created_by=instructor.id,
        )
        lab = LabInstance(
            template_id=template.id,
            owner_id=student.id,
            lab_name=f"attempt-lab-{slug_suffix}",
            lab_directory=f"/tmp/attempt-lab-{slug_suffix}",
        )
        session.add_all([ticket, lab])
        await session.flush()
        attempt = TicketAttempt(ticket_id=ticket.id, student_id=student.id, lab_instance_id=lab.id)
        session.add(attempt)
        await session.commit()
        await session.refresh(attempt)
        return attempt


async def test_admin_can_list_attempts(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    admin_token: str,
    active_template: LabTemplate,
    seeded_users: dict[str, User],
    auth_header,
) -> None:
    await _create_attempt(session_factory, active_template, seeded_users["instructor"], seeded_users["student"], "admin")

    response = await client.get("/api/v1/attempts", headers=auth_header(admin_token))

    assert response.status_code == 200
    assert len(response.json()) == 1


async def test_instructor_lists_only_attempts_for_own_tickets(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    instructor_token: str,
    active_template: LabTemplate,
    seeded_users: dict[str, User],
    auth_header,
) -> None:
    await _create_attempt(session_factory, active_template, seeded_users["instructor"], seeded_users["student"], "own")
    await _create_attempt(session_factory, active_template, seeded_users["instructor2"], seeded_users["student"], "other")

    response = await client.get("/api/v1/attempts", headers=auth_header(instructor_token))

    assert response.status_code == 200
    assert len(response.json()) == 1


async def test_student_lists_only_own_attempts_on_management_endpoint(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    student_token: str,
    active_template: LabTemplate,
    seeded_users: dict[str, User],
    auth_header,
) -> None:
    await _create_attempt(session_factory, active_template, seeded_users["instructor"], seeded_users["student"], "student")

    response = await client.get("/api/v1/attempts", headers=auth_header(student_token))

    assert response.status_code == 200
    assert len(response.json()) == 1
