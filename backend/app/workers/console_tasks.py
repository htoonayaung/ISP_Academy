import asyncio
import uuid

from app.adapters.lab_console_adapter import LabConsoleAdapter
from app.db.session import async_session_factory
from app.models import lab_instance, lab_template, user  # noqa: F401
from app.models.lab_instance import LabEvent, LabInstanceStatus
from app.repositories.labs import LabRepository
from app.workers.celery_app import celery_app


@celery_app.task(name="app.workers.console_tasks.execute_console_command_task")
def execute_console_command_task(
    lab_id: str,
    node_id: str,
    command: str,
    mode: str = "single",
    commands: list[str] | None = None,
) -> dict:
    return asyncio.run(_execute_console_command(uuid.UUID(lab_id), uuid.UUID(node_id), command, mode, commands or []))


async def _execute_console_command(
    lab_id: uuid.UUID,
    node_id: uuid.UUID,
    command: str,
    mode: str,
    commands: list[str],
) -> dict:
    async with async_session_factory() as session:
        repository = LabRepository(session)
        lab = await repository.get_by_id(lab_id)
        node = await repository.get_node_by_id(node_id)
        if lab is None or lab.status != LabInstanceStatus.RUNNING.value:
            return _error(command, "Lab state changed, refresh and try again")
        if node is None or node.lab_instance_id != lab.id or not node.container_name:
            return _error(command, "Node not found or console unavailable")

        adapter = LabConsoleAdapter()
        if node.kind.lower() == "frr":
            result = adapter.execute_frr_batch(node.container_name, commands) if mode == "batch" else adapter.execute_frr(node.container_name, command)
        elif node.kind.lower() == "linux":
            result = adapter.execute_linux(node.container_name, command)
        else:
            return _error(command, "Console not available for this node")

        await repository.add_event(
            LabEvent(
                lab_instance_id=lab.id,
                event_type="LAB_CONSOLE_COMMAND",
                message=f"Console command executed on node {node.name}",
                stdout=result.stdout,
                stderr=result.stderr,
            )
        )
        await repository.commit()
        return {
            "status": result.status,
            "command": result.command,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.exit_code,
            "duration_ms": result.duration_ms,
        }


def _error(command: str, message: str) -> dict:
    return {
        "status": "error",
        "command": command,
        "stdout": "",
        "stderr": message,
        "exit_code": 1,
        "duration_ms": 0,
    }
