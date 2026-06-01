import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.core.permissions import get_current_user
from app.models.user import User
from app.models.verification import VerificationRule, VerificationRun
from app.repositories.labs import LabRepository
from app.repositories.tickets import TicketRepository
from app.repositories.verification import VerificationRepository
from app.schemas.verification import VerificationRuleCreate, VerificationRuleRead, VerificationRuleUpdate, VerificationRunRead
from app.services.verification_service import VerificationService

router = APIRouter(tags=["verification"])
my_router = APIRouter(tags=["my-verification"])


def get_verification_service(session: AsyncSession = Depends(get_db_session)) -> VerificationService:
    return VerificationService(
        VerificationRepository(session),
        TicketRepository(session),
        LabRepository(session),
    )


@router.post("/tickets/{ticket_id}/verification-rules", response_model=VerificationRuleRead, status_code=status.HTTP_201_CREATED)
async def create_verification_rule(
    ticket_id: uuid.UUID,
    payload: VerificationRuleCreate,
    current_user: User = Depends(get_current_user),
    service: VerificationService = Depends(get_verification_service),
) -> VerificationRule:
    return await service.create_rule(current_user, ticket_id, payload)


@router.get("/tickets/{ticket_id}/verification-rules", response_model=list[VerificationRuleRead])
async def list_verification_rules(
    ticket_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: VerificationService = Depends(get_verification_service),
) -> list[VerificationRule]:
    return await service.list_rules(current_user, ticket_id)


@router.patch("/verification-rules/{rule_id}", response_model=VerificationRuleRead)
async def update_verification_rule(
    rule_id: uuid.UUID,
    payload: VerificationRuleUpdate,
    current_user: User = Depends(get_current_user),
    service: VerificationService = Depends(get_verification_service),
) -> VerificationRule:
    return await service.update_rule(current_user, rule_id, payload)


@router.delete("/verification-rules/{rule_id}", response_model=VerificationRuleRead)
async def delete_verification_rule(
    rule_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: VerificationService = Depends(get_verification_service),
) -> VerificationRule:
    return await service.delete_rule(current_user, rule_id)


@my_router.post("/attempts/{attempt_id}/verify", response_model=VerificationRunRead, status_code=status.HTTP_201_CREATED)
async def run_verification(
    attempt_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: VerificationService = Depends(get_verification_service),
) -> VerificationRunRead:
    run = await service.queue_verification(current_user, attempt_id)
    return VerificationRunRead.model_validate(run)


@my_router.get("/attempts/{attempt_id}/verification-runs", response_model=list[VerificationRunRead])
async def list_my_verification_runs(
    attempt_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: VerificationService = Depends(get_verification_service),
) -> list[VerificationRunRead]:
    runs = await service.list_runs_for_attempt(current_user, attempt_id)
    return [VerificationRunRead.model_validate(run) for run in runs]


@my_router.get("/verification-runs/{run_id}", response_model=VerificationRunRead)
async def get_my_verification_run(
    run_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: VerificationService = Depends(get_verification_service),
) -> VerificationRunRead:
    run = await service.get_run(current_user, run_id)
    results = await service.results_for_run(run.id)
    data = VerificationRunRead.model_validate(run)
    data.results = results
    return data
