import uuid

from fastapi import HTTPException, status

from app.models.lab_instance import LabInstance, LabInstanceStatus, LabNode
from app.models.user import User
from app.repositories.labs import LabRepository
from app.schemas.console import ConsoleExecuteRead, ConsoleNodeRead
from app.services.console_command_policy import ConsoleCommandPolicy
from app.services.lab_service import LabService


class ConsoleService:
    def __init__(
        self,
        lab_service: LabService,
        lab_repository: LabRepository,
        policy: ConsoleCommandPolicy | None = None,
    ) -> None:
        self.lab_service = lab_service
        self.lab_repository = lab_repository
        self.policy = policy or ConsoleCommandPolicy()

    async def list_console_nodes(self, actor: User, lab_id: uuid.UUID) -> list[ConsoleNodeRead]:
        lab = await self._get_running_lab(actor, lab_id)
        nodes = await self.lab_repository.list_nodes(lab.id)
        return [self._shape_console_node(node) for node in nodes if self._console_type(node) is not None]

    async def execute(self, actor: User, lab_id: uuid.UUID, node_id: uuid.UUID, command: str) -> ConsoleExecuteRead:
        lab, node = await self._get_console_node(actor, lab_id, node_id)
        safe_command = self.policy.validate(node.kind, command)
        from app.workers.console_tasks import execute_console_command_task

        result = execute_console_command_task.apply_async(
            kwargs={
                "lab_id": str(lab.id),
                "node_id": str(node.id),
                "command": safe_command,
                "mode": "single",
            }
        ).get(timeout=20)
        return ConsoleExecuteRead(**result)

    async def execute_batch(self, actor: User, lab_id: uuid.UUID, node_id: uuid.UUID, commands: list[str]) -> ConsoleExecuteRead:
        lab, node = await self._get_console_node(actor, lab_id, node_id)
        safe_commands = self.policy.validate_batch(node.kind, commands)
        from app.workers.console_tasks import execute_console_command_task

        result = execute_console_command_task.apply_async(
            kwargs={
                "lab_id": str(lab.id),
                "node_id": str(node.id),
                "command": "\n".join(safe_commands),
                "commands": safe_commands,
                "mode": "batch",
            }
        ).get(timeout=25)
        return ConsoleExecuteRead(**result)

    async def _get_console_node(self, actor: User, lab_id: uuid.UUID, node_id: uuid.UUID) -> tuple[LabInstance, LabNode]:
        lab = await self._get_running_lab(actor, lab_id)
        node = await self.lab_repository.get_node_by_id(node_id)
        if node is None or node.lab_instance_id != lab.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")
        if self._console_type(node) is None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Console not available for this node")
        if not node.container_name:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Console requires a known lab node container")
        return lab, node

    async def _get_running_lab(self, actor: User, lab_id: uuid.UUID) -> LabInstance:
        lab = await self.lab_service.get_lab(actor, lab_id)
        if lab.status != LabInstanceStatus.RUNNING.value:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Lab is not running")
        return lab

    def _shape_console_node(self, node: LabNode) -> ConsoleNodeRead:
        console_type = self._console_type(node)
        if console_type is None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Console not available for this node")
        return ConsoleNodeRead(
            id=node.id,
            name=node.name,
            kind=node.kind,
            status=node.status,
            management_ipv4=node.management_ipv4,
            console_type=console_type,
        )

    @staticmethod
    def _console_type(node: LabNode) -> str | None:
        kind = node.kind.lower()
        if kind == "frr":
            return "frr_vtysh"
        if kind == "linux":
            return "linux_safe"
        return None
