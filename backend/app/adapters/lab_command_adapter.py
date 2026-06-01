import shlex
import subprocess
from dataclasses import dataclass

from app.core.config import get_settings
from app.models.lab_instance import LabNode


@dataclass(frozen=True)
class LabCommandResult:
    exit_code: int
    stdout: str
    stderr: str


class LabCommandAdapter:
    def __init__(self, output_limit: int | None = None) -> None:
        settings = get_settings()
        self.output_limit = output_limit or settings.lab_event_output_limit

    def execute(self, node: LabNode, command: str, timeout_seconds: int) -> LabCommandResult:
        container_name = node.container_name or self._container_name_from_node(node)
        if not container_name:
            raise ValueError("Lab node does not have a known container name")

        args = shlex.split(command)
        if not args:
            raise ValueError("Verification command is empty")

        completed = subprocess.run(
            ["docker", "exec", container_name, *args],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        return LabCommandResult(
            exit_code=completed.returncode,
            stdout=self._limit(completed.stdout),
            stderr=self._limit(completed.stderr),
        )

    @staticmethod
    def _container_name_from_node(node: LabNode) -> str | None:
        if node.name.startswith("clab-"):
            return node.name
        return None

    def _limit(self, value: str) -> str:
        if len(value) <= self.output_limit:
            return value
        return value[: self.output_limit] + "\n[output truncated]"
