import asyncio
import uuid
from datetime import UTC, datetime

from app.adapters.lab_command_adapter import LabCommandAdapter
from app.db.session import async_session_factory
from app.models import lab_instance, lab_template, ticket, user  # noqa: F401
from app.models.verification import VerificationResult, VerificationResultStatus, VerificationRunStatus
from app.repositories.labs import LabRepository
from app.repositories.tickets import TicketRepository
from app.repositories.verification import VerificationRepository
from app.services.verification_service import evaluate_assertion
from app.workers.celery_app import celery_app


@celery_app.task(name="app.workers.verification_tasks.run_verification_task")
def run_verification_task(run_id: str) -> None:
    asyncio.run(_run_verification(uuid.UUID(run_id)))


async def _run_verification(run_id: uuid.UUID) -> None:
    async with async_session_factory() as session:
        verification_repository = VerificationRepository(session)
        ticket_repository = TicketRepository(session)
        lab_repository = LabRepository(session)
        run = await verification_repository.get_run_by_id(run_id)
        if run is None or run.status != VerificationRunStatus.QUEUED.value:
            return

        run.status = VerificationRunStatus.RUNNING.value
        run.started_at = datetime.now(UTC)
        await verification_repository.commit()

        attempt = await ticket_repository.get_attempt_by_id(run.ticket_attempt_id)
        if attempt is None:
            await _mark_run_error(verification_repository, run, "Ticket attempt not found")
            return

        lab = await lab_repository.get_by_id(attempt.lab_instance_id)
        if lab is None or lab.status != "RUNNING":
            await _mark_run_error(verification_repository, run, "Linked lab is not running")
            return

        rules = await verification_repository.list_active_rules_for_ticket(attempt.ticket_id)
        nodes = await lab_repository.list_nodes(lab.id)
        adapter = LabCommandAdapter()
        any_failed = False
        any_error = False

        for rule in rules:
            node = _find_node(nodes, rule.target_node)
            if node is None:
                any_error = True
                await verification_repository.add_result(
                    VerificationResult(
                        verification_run_id=run.id,
                        verification_rule_id=rule.id,
                        status=VerificationResultStatus.ERROR.value,
                        actual_output=None,
                        message="Target node was not found in the lab instance",
                    )
                )
                continue
            try:
                command_result = adapter.execute(node, rule.command, rule.timeout_seconds)
                combined_output = (command_result.stdout or "") + (command_result.stderr or "")
                outcome = evaluate_assertion(
                    rule.assertion_type,
                    rule.expected_value,
                    combined_output,
                    command_result.exit_code,
                )
                if not outcome.passed:
                    any_failed = True
                await verification_repository.add_result(
                    VerificationResult(
                        verification_run_id=run.id,
                        verification_rule_id=rule.id,
                        status=VerificationResultStatus.PASSED.value if outcome.passed else VerificationResultStatus.FAILED.value,
                        actual_output=combined_output,
                        message=outcome.message,
                    )
                )
            except Exception:
                any_error = True
                await verification_repository.add_result(
                    VerificationResult(
                        verification_run_id=run.id,
                        verification_rule_id=rule.id,
                        status=VerificationResultStatus.ERROR.value,
                        actual_output=None,
                        message="Verification command failed to execute safely",
                    )
                )

        run.finished_at = datetime.now(UTC)
        if any_error:
            run.status = VerificationRunStatus.ERROR.value
        elif any_failed:
            run.status = VerificationRunStatus.FAILED.value
        else:
            run.status = VerificationRunStatus.PASSED.value
        await verification_repository.commit()


async def _mark_run_error(repository: VerificationRepository, run, message: str) -> None:
    run.status = VerificationRunStatus.ERROR.value
    run.finished_at = datetime.now(UTC)
    await repository.commit()


def _find_node(nodes, target_node: str):
    for node in nodes:
        if node.name == target_node or node.container_name == target_node:
            return node
        if node.name.endswith(f"-{target_node}"):
            return node
    return None
