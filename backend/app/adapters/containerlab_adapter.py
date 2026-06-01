import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from app.core.config import get_settings
from app.models.lab_instance import LabInstance


@dataclass(frozen=True)
class ContainerlabResult:
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


class ContainerlabAdapter:
    def __init__(
        self,
        lab_root: str | None = None,
        binary: str | None = None,
        timeout_seconds: int | None = None,
        output_limit: int | None = None,
    ) -> None:
        settings = get_settings()
        self.lab_root = Path(lab_root or settings.lab_root).resolve()
        self.binary = binary or settings.containerlab_bin
        self.timeout_seconds = timeout_seconds or settings.containerlab_command_timeout_seconds
        self.output_limit = output_limit or settings.lab_event_output_limit

    def deploy(self, lab_instance: LabInstance) -> ContainerlabResult:
        return self._run(["deploy", "-t", str(self._lab_file(lab_instance))])

    def destroy(self, lab_instance: LabInstance) -> ContainerlabResult:
        return self._run(["destroy", "-t", str(self._lab_file(lab_instance))])

    def inspect(self, lab_instance: LabInstance) -> tuple[ContainerlabResult, object | None]:
        result = self._run(["inspect", "-t", str(self._lab_file(lab_instance)), "--format", "json"])
        parsed: object | None = None
        if result.ok and result.stdout:
            try:
                parsed = json.loads(result.stdout)
            except json.JSONDecodeError:
                parsed = None
        return result, parsed

    def save_lab_file(self, lab_instance: LabInstance, rendered_yaml: str) -> Path:
        directory = Path(lab_instance.lab_directory).resolve()
        self.validate_lab_path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        lab_file = (directory / "clab.yml").resolve()
        self.validate_lab_path(lab_file)
        lab_file.write_text(rendered_yaml, encoding="utf-8")
        return lab_file

    def validate_lab_path(self, path: str | Path) -> Path:
        resolved = Path(path).resolve()
        if resolved != self.lab_root and self.lab_root not in resolved.parents:
            raise ValueError("Lab path must stay inside LAB_ROOT")
        return resolved

    def _lab_file(self, lab_instance: LabInstance) -> Path:
        lab_file = (Path(lab_instance.lab_directory).resolve() / "clab.yml").resolve()
        self.validate_lab_path(lab_file)
        return lab_file

    def _run(self, args: list[str]) -> ContainerlabResult:
        command = [self.binary, *args]
        try:
            completed = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )
            return ContainerlabResult(
                returncode=completed.returncode,
                stdout=self._limit(completed.stdout),
                stderr=self._limit(completed.stderr),
            )
        except subprocess.TimeoutExpired as exc:
            return ContainerlabResult(
                returncode=124,
                stdout=self._limit(exc.stdout if isinstance(exc.stdout, str) else ""),
                stderr="Containerlab command timed out",
            )

    def _limit(self, value: str) -> str:
        if len(value) <= self.output_limit:
            return value
        return value[: self.output_limit] + "\n[output truncated]"
