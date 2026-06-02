import uuid
from dataclasses import dataclass

from fastapi import HTTPException, status

from app.models.lab_instance import LabInstanceStatus
from app.models.ticket import Ticket, TicketAttempt
from app.models.user import User, UserRole
from app.models.verification import VerificationResult, VerificationRule, VerificationRun, VerificationRunStatus
from app.repositories.labs import LabRepository
from app.repositories.tickets import TicketRepository
from app.repositories.verification import VerificationRepository
from app.schemas.verification import VerificationRuleCreate, VerificationRuleUpdate


@dataclass(frozen=True)
class AssertionOutcome:
    passed: bool
    message: str


class VerificationService:
    def __init__(
        self,
        repository: VerificationRepository,
        ticket_repository: TicketRepository,
        lab_repository: LabRepository,
    ) -> None:
        self.repository = repository
        self.ticket_repository = ticket_repository
        self.lab_repository = lab_repository

    async def create_rule(self, actor: User, ticket_id: uuid.UUID, data: VerificationRuleCreate) -> VerificationRule:
        ticket = await self._get_ticket_for_rule_management(actor, ticket_id)
        rule = VerificationRule(
            ticket_id=ticket.id,
            name=data.name,
            target_node=data.target_node,
            command=data.command,
            parser_type=data.parser_type.value,
            assertion_type=data.assertion_type.value,
            expected_value=data.expected_value,
            timeout_seconds=data.timeout_seconds,
            is_active=data.is_active,
        )
        created = await self.repository.create_rule(rule)
        await self.repository.commit()
        await self.repository.refresh(created)
        return created

    async def list_rules(self, actor: User, ticket_id: uuid.UUID) -> list[VerificationRule]:
        await self._get_ticket_for_rule_management(actor, ticket_id)
        return await self.repository.list_rules_for_ticket(ticket_id)

    async def update_rule(self, actor: User, rule_id: uuid.UUID, data: VerificationRuleUpdate) -> VerificationRule:
        rule = await self.repository.get_rule_by_id(rule_id)
        if rule is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Verification rule not found")
        await self._get_ticket_for_rule_management(actor, rule.ticket_id)

        if data.name is not None:
            rule.name = data.name
        if data.target_node is not None:
            rule.target_node = data.target_node
        if data.command is not None:
            rule.command = data.command
        if data.parser_type is not None:
            rule.parser_type = data.parser_type.value
        if data.assertion_type is not None:
            rule.assertion_type = data.assertion_type.value
        if data.expected_value is not None:
            rule.expected_value = data.expected_value
        if data.timeout_seconds is not None:
            rule.timeout_seconds = data.timeout_seconds
        if data.is_active is not None:
            rule.is_active = data.is_active
        await self.repository.commit()
        await self.repository.refresh(rule)
        return rule

    async def delete_rule(self, actor: User, rule_id: uuid.UUID) -> VerificationRule:
        rule = await self.repository.get_rule_by_id(rule_id)
        if rule is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Verification rule not found")
        await self._get_ticket_for_rule_management(actor, rule.ticket_id)
        rule.is_active = False
        await self.repository.commit()
        await self.repository.refresh(rule)
        return rule

    async def hard_delete_rule(self, actor: User, rule_id: uuid.UUID) -> None:
        rule = await self.repository.get_rule_by_id(rule_id)
        if rule is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Verification rule not found")
        await self._get_ticket_for_rule_management(actor, rule.ticket_id)
        if await self.repository.count_results_for_rule(rule.id) > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Verification rule has run history; deactivate instead",
            )
        await self.repository.delete_rule(rule)
        await self.repository.commit()

    async def queue_verification(self, actor: User, attempt_id: uuid.UUID) -> VerificationRun:
        attempt = await self._get_own_attempt(actor, attempt_id)
        lab = await self.lab_repository.get_by_id(attempt.lab_instance_id)
        if lab is None or lab.status != LabInstanceStatus.RUNNING.value:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Verification requires a running lab")
        rules = await self.repository.list_active_rules_for_ticket(attempt.ticket_id)
        if not rules:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No active verification rules exist")

        run = VerificationRun(ticket_attempt_id=attempt.id, status=VerificationRunStatus.QUEUED.value)
        created = await self.repository.create_run(run)
        await self.repository.commit()
        await self.repository.refresh(created)
        from app.workers.verification_tasks import run_verification_task

        run_verification_task.delay(str(created.id))
        return created

    async def list_runs_for_attempt(self, actor: User, attempt_id: uuid.UUID) -> list[VerificationRun]:
        attempt = await self._get_own_attempt(actor, attempt_id)
        return await self.repository.list_runs_for_attempt(attempt.id)

    async def list_runs_for_attempt_management(self, actor: User, attempt_id: uuid.UUID) -> list[VerificationRun]:
        attempt = await self.ticket_repository.get_attempt_by_id(attempt_id)
        if attempt is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket attempt not found")
        if actor.role == UserRole.ADMIN:
            return await self.repository.list_runs_for_attempt(attempt.id)
        if actor.role == UserRole.INSTRUCTOR:
            ticket = await self.ticket_repository.get_by_id(attempt.ticket_id)
            if ticket is not None and ticket.created_by == actor.id:
                return await self.repository.list_runs_for_attempt(attempt.id)
        if actor.role == UserRole.STUDENT and attempt.student_id == actor.id:
            return await self.repository.list_runs_for_attempt(attempt.id)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    async def get_run(self, actor: User, run_id: uuid.UUID) -> VerificationRun:
        run = await self.repository.get_run_by_id(run_id)
        if run is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Verification run not found")
        await self._get_own_attempt(actor, run.ticket_attempt_id)
        return run

    async def results_for_run(self, run_id: uuid.UUID) -> list[VerificationResult]:
        return await self.repository.list_results_for_run(run_id)

    async def _get_ticket_for_rule_management(self, actor: User, ticket_id: uuid.UUID) -> Ticket:
        ticket = await self.ticket_repository.get_by_id(ticket_id)
        if ticket is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
        if actor.role == UserRole.ADMIN:
            return ticket
        if actor.role == UserRole.INSTRUCTOR and ticket.created_by == actor.id:
            return ticket
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    async def _get_own_attempt(self, actor: User, attempt_id: uuid.UUID) -> TicketAttempt:
        if actor.role != UserRole.STUDENT:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only students can run verification")
        attempt = await self.ticket_repository.get_attempt_by_id(attempt_id)
        if attempt is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket attempt not found")
        if attempt.student_id != actor.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
        return attempt


def evaluate_assertion(assertion_type: str, expected_value: str | None, output: str, exit_code: int) -> AssertionOutcome:
    expected = expected_value or ""
    stripped = output.strip()
    if assertion_type == "CONTAINS":
        passed = expected in output
        return AssertionOutcome(passed, "Expected text found" if passed else "Expected text was not found")
    if assertion_type == "NOT_CONTAINS":
        passed = expected not in output
        return AssertionOutcome(passed, "Unexpected text absent" if passed else "Unexpected text was found")
    if assertion_type == "EQUALS":
        passed = stripped == expected
        return AssertionOutcome(passed, "Output matched expected value" if passed else "Output did not match expected value")
    if assertion_type == "EXIT_CODE_ZERO":
        passed = exit_code == 0
        return AssertionOutcome(passed, "Command exited successfully" if passed else "Command returned a non-zero exit code")
    if assertion_type == "BGP_NEIGHBOR_ESTABLISHED":
        passed = "Established" in output or "established" in output
        return AssertionOutcome(passed, "BGP neighbor is established" if passed else "BGP neighbor is not established")
    if assertion_type == "ROUTE_EXISTS":
        passed = expected in output
        return AssertionOutcome(passed, "Route exists" if passed else "Route was not found")
    return AssertionOutcome(False, "Unsupported assertion type")
