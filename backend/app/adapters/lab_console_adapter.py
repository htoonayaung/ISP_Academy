import subprocess
import time
from dataclasses import dataclass

from app.core.config import get_settings


@dataclass(frozen=True)
class LabConsoleResult:
    status: str
    command: str
    stdout: str
    stderr: str
    exit_code: int
    duration_ms: int


class LabConsoleAdapter:
    def __init__(self, output_limit: int | None = None, timeout_seconds: int = 15) -> None:
        settings = get_settings()
        self.output_limit = output_limit or settings.lab_event_output_limit
        self.timeout_seconds = timeout_seconds

    def execute_frr(self, container_name: str, command: str) -> LabConsoleResult:
        return self._run(command, ["docker", "exec", container_name, "vtysh", "-c", command])

    def execute_frr_batch(self, container_name: str, commands: list[str]) -> LabConsoleResult:
        args = ["docker", "exec", container_name, "vtysh"]
        for command in commands:
            args.extend(["-c", command])
        return self._run("\n".join(commands), args)

    def execute_linux(self, container_name: str, command: str) -> LabConsoleResult:
        return self._run(command, ["docker", "exec", container_name, *command.split()])

    def _run(self, command: str, args: list[str]) -> LabConsoleResult:
        started = time.monotonic()
        try:
            completed = subprocess.run(
                args,
                check=False,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )
            duration_ms = int((time.monotonic() - started) * 1000)
            return LabConsoleResult(
                status="ok" if completed.returncode == 0 else "error",
                command=command,
                stdout=self._limit(completed.stdout),
                stderr=self._limit(completed.stderr),
                exit_code=completed.returncode,
                duration_ms=duration_ms,
            )
        except subprocess.TimeoutExpired:
            return LabConsoleResult(
                status="timeout",
                command=command,
                stdout="",
                stderr="Command timed out",
                exit_code=124,
                duration_ms=int((time.monotonic() - started) * 1000),
            )

    def _limit(self, value: str) -> str:
        if len(value) <= self.output_limit:
            return value
        return value[: self.output_limit] + "\n[output truncated]"
