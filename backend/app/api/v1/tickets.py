import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.core.permissions import get_current_user
from app.models.ticket import Ticket, TicketAttempt
from app.models.user import User
from app.repositories.lab_templates import LabTemplateRepository
from app.repositories.labs import LabRepository
from app.repositories.tickets import TicketRepository
from app.schemas.ticket import TicketAttemptRead, TicketCreate, TicketUpdate
from app.services.ticket_service import TicketService

router = APIRouter(tags=["tickets"])
my_router = APIRouter(tags=["my-attempts"])
attempts_router = APIRouter(tags=["attempts"])


def get_ticket_service(session: AsyncSession = Depends(get_db_session)) -> TicketService:
    return TicketService(
        TicketRepository(session),
        LabTemplateRepository(session),
        LabRepository(session),
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_ticket(
    payload: TicketCreate,
    current_user: User = Depends(get_current_user),
    service: TicketService = Depends(get_ticket_service),
) -> dict:
    ticket = await service.create_ticket(current_user, payload)
    return service.shape_ticket(current_user, ticket)


@router.get("")
async def list_tickets(
    current_user: User = Depends(get_current_user),
    service: TicketService = Depends(get_ticket_service),
) -> list[dict]:
    tickets = await service.list_tickets(current_user)
    return [service.shape_ticket(current_user, ticket) for ticket in tickets]


@router.get("/{ticket_id}")
async def get_ticket(
    ticket_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: TicketService = Depends(get_ticket_service),
) -> dict:
    ticket = await service.get_ticket(current_user, ticket_id)
    return service.shape_ticket(current_user, ticket)


@router.patch("/{ticket_id}")
async def update_ticket(
    ticket_id: uuid.UUID,
    payload: TicketUpdate,
    current_user: User = Depends(get_current_user),
    service: TicketService = Depends(get_ticket_service),
) -> dict:
    ticket = await service.update_ticket(current_user, ticket_id, payload)
    return service.shape_ticket(current_user, ticket)


@router.delete("/{ticket_id}")
async def delete_ticket(
    ticket_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: TicketService = Depends(get_ticket_service),
) -> dict:
    ticket = await service.archive_ticket(current_user, ticket_id)
    return service.shape_ticket(current_user, ticket)


@router.delete("/{ticket_id}/hard-delete", status_code=status.HTTP_204_NO_CONTENT)
async def hard_delete_ticket(
    ticket_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: TicketService = Depends(get_ticket_service),
) -> None:
    await service.hard_delete_ticket(current_user, ticket_id)


@router.post("/{ticket_id}/publish")
async def publish_ticket(
    ticket_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: TicketService = Depends(get_ticket_service),
) -> dict:
    ticket = await service.publish_ticket(current_user, ticket_id)
    return service.shape_ticket(current_user, ticket)


@router.post("/{ticket_id}/archive")
async def archive_ticket(
    ticket_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: TicketService = Depends(get_ticket_service),
) -> dict:
    ticket = await service.archive_ticket(current_user, ticket_id)
    return service.shape_ticket(current_user, ticket)


@router.post("/{ticket_id}/start", response_model=TicketAttemptRead, status_code=status.HTTP_201_CREATED)
async def start_ticket_attempt(
    ticket_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: TicketService = Depends(get_ticket_service),
) -> TicketAttempt:
    return await service.start_attempt(current_user, ticket_id)


@my_router.get("/attempts", response_model=list[TicketAttemptRead])
async def list_my_attempts(
    current_user: User = Depends(get_current_user),
    service: TicketService = Depends(get_ticket_service),
) -> list[TicketAttempt]:
    return await service.list_my_attempts(current_user)


@my_router.get("/attempts/{attempt_id}", response_model=TicketAttemptRead)
async def get_my_attempt(
    attempt_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: TicketService = Depends(get_ticket_service),
) -> TicketAttempt:
    return await service.get_my_attempt(current_user, attempt_id)


@attempts_router.get("", response_model=list[TicketAttemptRead])
async def list_attempts(
    current_user: User = Depends(get_current_user),
    service: TicketService = Depends(get_ticket_service),
) -> list[TicketAttempt]:
    return await service.list_attempts(current_user)


@attempts_router.get("/{attempt_id}", response_model=TicketAttemptRead)
async def get_attempt(
    attempt_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: TicketService = Depends(get_ticket_service),
) -> TicketAttempt:
    return await service.get_attempt(current_user, attempt_id)


@attempts_router.delete("/{attempt_id}/hard-delete", status_code=status.HTTP_204_NO_CONTENT)
async def hard_delete_attempt(
    attempt_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: TicketService = Depends(get_ticket_service),
) -> None:
    await service.hard_delete_attempt(current_user, attempt_id)
