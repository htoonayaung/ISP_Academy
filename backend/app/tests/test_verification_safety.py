import inspect
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.adapters.lab_command_adapter import LabCommandAdapter
from app.models.lab_instance import LabInstance, LabNode
from app.models.lab_template import LabTemplate
from app.models.ticket import Ticket, TicketAttempt
from app.models.user import User
from app.models.verification import VerificationResult, VerificationRule, VerificationRun
from app.repositories.verification import VerificationRepository
from app.services.verification_service import evaluate_assertion
from app.workers.verification_tasks import _run_verification


def test_lab_command_adapter_does_not_use_shell_true() -> None:
    source = inspect.getsource(LabCommandAdapter.execute)

    assert "shell=True" not in source


def test_assertion_engine_checks_simple_results() -> None:
    assert evaluate_assertion("CONTAINS", "ok", "status ok", 0).passed is True
    assert evaluate_assertion("NOT_CONTAINS", "down", "status ok", 0).passed is True
    assert evaluate_assertion("EQUALS", "ok", "ok\n", 0).passed is True
    assert evaluate_assertion("EXIT_CODE_ZERO", None, "", 0).passed is True
    assert evaluate_assertion("ROUTE_EXISTS", "10.0.0.0/24", "*> 10.0.0.0/24", 0).passed is True


def test_lab_command_adapter_rejects_unknown_container() -> None:
    adapter = LabCommandAdapter()
    node = LabNode(
        lab_instance_id=uuid.uuid4(),
        name="host1",
        kind="linux",
        container_name=None,
        status="running",
    )

    with pytest.raises(ValueError):
        adapter.execute(node, "echo ok", 1)


@pytest.mark.asyncio
async def test_verification_task_uses_rule_command_and_stores_result(
    session_factory: async_sessionmaker[AsyncSession],
    active_template: LabTemplate,
    seeded_users: dict[str, User],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    commands: list[str] = []

    class Result:
        exit_code = 0
        stdout = "hello ok"
        stderr = ""

    class Adapter:
        def execute(self, node, command: str, timeout_seconds: int):
            commands.append(command)
            return Result()

    monkeypatch.setattr("app.workers.verification_tasks.LabCommandAdapter", Adapter)
    async with session_factory() as session:
        ticket = Ticket(
            lab_template_id=active_template.id,
            title="Verification Safety Ticket",
            slug="verification-safety-ticket",
            description="desc",
            student_instructions="instructions",
            status="PUBLISHED",
            created_by=seeded_users["admin"].id,
        )
        session.add(ticket)
        await session.flush()
        lab = LabInstance(
            template_id=active_template.id,
            owner_id=seeded_users["student"].id,
            status="RUNNING",
            lab_name="isp-verification-safety",
            lab_directory="/tmp/isp-academy-test-labs/instances/verify",
        )
        session.add(lab)
        await session.flush()
        node = LabNode(
            lab_instance_id=lab.id,
            name="host1",
            kind="linux",
            container_name="clab-test-host1",
            status="running",
        )
        session.add(node)
        attempt = TicketAttempt(
            ticket_id=ticket.id,
            student_id=seeded_users["student"].id,
            lab_instance_id=lab.id,
            status="STARTED",
        )
        session.add(attempt)
        await session.flush()
        rule = VerificationRule(
            ticket_id=ticket.id,
            name="Rule command",
            target_node="host1",
            command="echo ok",
            parser_type="SIMPLE_TEXT",
            assertion_type="CONTAINS",
            expected_value="ok",
            timeout_seconds=5,
            is_active=True,
        )
        session.add(rule)
        run = VerificationRun(ticket_attempt_id=attempt.id, status="QUEUED")
        session.add(run)
        await session.commit()
        run_id = run.id

    monkeypatch.setattr("app.workers.verification_tasks.async_session_factory", session_factory)
    await _run_verification(run_id)

    async with session_factory() as session:
        repository = VerificationRepository(session)
        run = await repository.get_run_by_id(run_id)
        results = await repository.list_results_for_run(run_id)

    assert commands == ["echo ok"]
    assert run is not None
    assert run.status == "PASSED"
    assert len(results) == 1
    assert results[0].status == "PASSED"
    assert results[0].actual_output == "hello ok"
