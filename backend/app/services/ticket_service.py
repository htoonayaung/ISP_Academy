import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.lab_runtime.name_sanitizer import slugify
from app.models.ticket import Ticket, TicketAttempt, TicketAttemptStatus, TicketStatus
from app.models.user import User, UserRole
from app.repositories.lab_templates import LabTemplateRepository
from app.repositories.labs import LabRepository
from app.repositories.tickets import TicketRepository
from app.schemas.lab_instance import LabCreate
from app.schemas.ticket import TicketCreate, TicketUpdate
from app.services.lab_service import LabService


class TicketService:
    def __init__(
        self,
        repository: TicketRepository,
        template_repository: LabTemplateRepository,
        lab_repository: LabRepository,
    ) -> None:
        self.repository = repository
        self.template_repository = template_repository
        self.lab_repository = lab_repository

    async def create_ticket(self, actor: User, data: TicketCreate) -> Ticket:
        self._require_admin_or_instructor(actor)
        await self._require_existing_template(data.lab_template_id)
        ticket = Ticket(
            lab_template_id=data.lab_template_id,
            title=data.title,
            slug=await self._unique_slug(data.title),
            description=data.description,
            student_instructions=data.student_instructions,
            hints=data.hints,
            hidden_solution=data.hidden_solution,
            status=data.status.value,
            created_by=actor.id,
            published_at=datetime.now(UTC) if data.status.value == TicketStatus.PUBLISHED.value else None,
        )
        try:
            created = await self.repository.create(ticket)
            await self.repository.commit()
            await self.repository.refresh(created)
            return created
        except IntegrityError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ticket slug already exists") from exc

    async def list_tickets(self, actor: User) -> list[Ticket]:
        if actor.role in {UserRole.ADMIN, UserRole.INSTRUCTOR}:
            return await self.repository.list_all()
        return await self.repository.list_published()

    async def get_ticket(self, actor: User, ticket_id: uuid.UUID) -> Ticket:
        ticket = await self.repository.get_by_id(ticket_id)
        if ticket is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
        self._require_ticket_view(actor, ticket)
        return ticket

    async def update_ticket(self, actor: User, ticket_id: uuid.UUID, data: TicketUpdate) -> Ticket:
        ticket = await self.get_ticket(actor, ticket_id)
        self._require_owner_or_admin(actor, ticket)

        if data.lab_template_id is not None:
            await self._require_existing_template(data.lab_template_id)
            ticket.lab_template_id = data.lab_template_id
        if data.title is not None:
            ticket.title = data.title
            ticket.slug = await self._unique_slug(data.title, exclude_id=ticket.id)
        if data.description is not None:
            ticket.description = data.description
        if data.student_instructions is not None:
            ticket.student_instructions = data.student_instructions
        if data.hints is not None:
            ticket.hints = data.hints
        if data.hidden_solution is not None:
            ticket.hidden_solution = data.hidden_solution
        if data.status is not None:
            ticket.status = data.status.value
            ticket.published_at = datetime.now(UTC) if data.status.value == TicketStatus.PUBLISHED.value else ticket.published_at

        try:
            await self.repository.commit()
            await self.repository.refresh(ticket)
            return ticket
        except IntegrityError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ticket slug already exists") from exc

    async def archive_ticket(self, actor: User, ticket_id: uuid.UUID) -> Ticket:
        ticket = await self.get_ticket(actor, ticket_id)
        self._require_owner_or_admin(actor, ticket)
        ticket.status = TicketStatus.ARCHIVED.value
        await self.repository.commit()
        await self.repository.refresh(ticket)
        return ticket

    async def publish_ticket(self, actor: User, ticket_id: uuid.UUID) -> Ticket:
        ticket = await self.get_ticket(actor, ticket_id)
        self._require_owner_or_admin(actor, ticket)
        template = await self.template_repository.get_by_id(ticket.lab_template_id)
        if template is None or not template.is_active:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ticket lab template must be active")
        ticket.status = TicketStatus.PUBLISHED.value
        ticket.published_at = datetime.now(UTC)
        await self.repository.commit()
        await self.repository.refresh(ticket)
        return ticket

    async def start_attempt(self, actor: User, ticket_id: uuid.UUID) -> TicketAttempt:
        if actor.role != UserRole.STUDENT:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only students can start ticket attempts")
        ticket = await self.repository.get_by_id(ticket_id)
        if ticket is None or ticket.status != TicketStatus.PUBLISHED.value:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Published ticket not found")
        template = await self.template_repository.get_by_id(ticket.lab_template_id)
        if template is None or not template.is_active:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ticket lab template is not active")

        lab_service = LabService(self.lab_repository, self.template_repository)
        lab = await lab_service.create_lab(actor, LabCreate(template_id=ticket.lab_template_id))
        attempt = TicketAttempt(
            ticket_id=ticket.id,
            student_id=actor.id,
            lab_instance_id=lab.id,
            status=TicketAttemptStatus.STARTED.value,
        )
        created = await self.repository.create_attempt(attempt)
        await self.repository.commit()
        await self.repository.refresh(created)
        return created

    async def list_my_attempts(self, actor: User) -> list[TicketAttempt]:
        if actor.role != UserRole.STUDENT:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only students can view own attempts")
        return await self.repository.list_attempts_by_student(actor.id)

    async def list_attempts(self, actor: User) -> list[TicketAttempt]:
        if actor.role == UserRole.ADMIN:
            return await self.repository.list_attempts_all()
        if actor.role == UserRole.INSTRUCTOR:
            return await self.repository.list_attempts_for_ticket_owner(actor.id)
        return await self.repository.list_attempts_by_student(actor.id)

    async def get_attempt(self, actor: User, attempt_id: uuid.UUID) -> TicketAttempt:
        attempt = await self.repository.get_attempt_by_id(attempt_id)
        if attempt is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket attempt not found")
        if actor.role == UserRole.ADMIN:
            return attempt
        if actor.role == UserRole.INSTRUCTOR:
            ticket = await self.repository.get_by_id(attempt.ticket_id)
            if ticket is not None and ticket.created_by == actor.id:
                return attempt
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
        if attempt.student_id == actor.id:
            return attempt
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    async def get_my_attempt(self, actor: User, attempt_id: uuid.UUID) -> TicketAttempt:
        if actor.role != UserRole.STUDENT:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only students can view own attempts")
        attempt = await self.repository.get_attempt_by_id(attempt_id)
        if attempt is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket attempt not found")
        if attempt.student_id != actor.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
        return attempt

    @staticmethod
    def shape_ticket(actor: User, ticket: Ticket) -> dict:
        data = {
            "id": ticket.id,
            "lab_template_id": ticket.lab_template_id,
            "title": ticket.title,
            "slug": ticket.slug,
            "description": ticket.description,
            "student_instructions": ticket.student_instructions,
            "hints": ticket.hints,
            "status": ticket.status,
            "created_by": ticket.created_by,
            "published_at": ticket.published_at,
            "created_at": ticket.created_at,
            "updated_at": ticket.updated_at,
        }
        if actor.role == UserRole.ADMIN or (actor.role == UserRole.INSTRUCTOR and ticket.created_by == actor.id):
            data["hidden_solution"] = ticket.hidden_solution
        return data

    async def _unique_slug(self, title: str, exclude_id: uuid.UUID | None = None) -> str:
        base_slug = slugify(title)
        candidate = base_slug
        suffix = 2
        while True:
            existing = await self.repository.get_by_slug(candidate)
            if existing is None or existing.id == exclude_id:
                return candidate
            candidate = f"{base_slug}-{suffix}"
            suffix += 1

    async def _require_existing_template(self, template_id: uuid.UUID) -> None:
        template = await self.template_repository.get_by_id(template_id)
        if template is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lab template not found")

    @staticmethod
    def _require_admin_or_instructor(actor: User) -> None:
        if actor.role not in {UserRole.ADMIN, UserRole.INSTRUCTOR}:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    @staticmethod
    def _require_owner_or_admin(actor: User, ticket: Ticket) -> None:
        if actor.role == UserRole.ADMIN:
            return
        if actor.role == UserRole.INSTRUCTOR and ticket.created_by == actor.id:
            return
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    @staticmethod
    def _require_ticket_view(actor: User, ticket: Ticket) -> None:
        if actor.role == UserRole.ADMIN:
            return
        if actor.role == UserRole.INSTRUCTOR:
            return
        if ticket.status == TicketStatus.PUBLISHED.value:
            return
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
