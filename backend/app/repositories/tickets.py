import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ticket import Ticket, TicketAttempt, TicketStatus


class TicketRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, ticket_id: str | uuid.UUID) -> Ticket | None:
        try:
            parsed_id = uuid.UUID(str(ticket_id))
        except ValueError:
            return None
        return await self.session.get(Ticket, parsed_id)

    async def get_by_slug(self, slug: str) -> Ticket | None:
        result = await self.session.execute(select(Ticket).where(Ticket.slug == slug))
        return result.scalar_one_or_none()

    async def list_all(self) -> list[Ticket]:
        result = await self.session.execute(select(Ticket).order_by(Ticket.created_at.desc()))
        return list(result.scalars().all())

    async def list_published(self) -> list[Ticket]:
        result = await self.session.execute(
            select(Ticket)
            .where(Ticket.status == TicketStatus.PUBLISHED.value)
            .order_by(Ticket.published_at.desc(), Ticket.created_at.desc())
        )
        return list(result.scalars().all())

    async def create(self, ticket: Ticket) -> Ticket:
        self.session.add(ticket)
        await self.session.flush()
        await self.session.refresh(ticket)
        return ticket

    async def create_attempt(self, attempt: TicketAttempt) -> TicketAttempt:
        self.session.add(attempt)
        await self.session.flush()
        await self.session.refresh(attempt)
        return attempt

    async def get_attempt_by_id(self, attempt_id: str | uuid.UUID) -> TicketAttempt | None:
        try:
            parsed_id = uuid.UUID(str(attempt_id))
        except ValueError:
            return None
        return await self.session.get(TicketAttempt, parsed_id)

    async def list_attempts_by_student(self, student_id: uuid.UUID) -> list[TicketAttempt]:
        result = await self.session.execute(
            select(TicketAttempt)
            .where(TicketAttempt.student_id == student_id)
            .order_by(TicketAttempt.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_attempts_all(self) -> list[TicketAttempt]:
        result = await self.session.execute(select(TicketAttempt).order_by(TicketAttempt.created_at.desc()))
        return list(result.scalars().all())

    async def list_attempts_for_ticket_owner(self, owner_id: uuid.UUID) -> list[TicketAttempt]:
        result = await self.session.execute(
            select(TicketAttempt)
            .join(Ticket, Ticket.id == TicketAttempt.ticket_id)
            .where(Ticket.created_by == owner_id)
            .order_by(TicketAttempt.created_at.desc())
        )
        return list(result.scalars().all())

    async def commit(self) -> None:
        await self.session.commit()

    async def refresh(self, item: Ticket | TicketAttempt) -> None:
        await self.session.refresh(item)
