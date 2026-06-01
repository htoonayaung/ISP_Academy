import uuid
from pathlib import Path

from app.core.config import get_settings
from app.lab_runtime.name_sanitizer import slugify


class LabDirectoryManager:
    def __init__(self, lab_root: str | None = None) -> None:
        settings = get_settings()
        self.lab_root = Path(lab_root or settings.lab_root).resolve()

    def instance_directory(self, lab_id: uuid.UUID) -> Path:
        directory = (self.lab_root / "instances" / str(lab_id)).resolve()
        self.validate_inside_lab_root(directory)
        return directory

    def create_instance_directory(self, lab_id: uuid.UUID) -> Path:
        directory = self.instance_directory(lab_id)
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    def lab_name(self, template_slug: str, lab_id: uuid.UUID) -> str:
        return f"isp-{slugify(template_slug)}-{str(lab_id)[:8]}"

    def validate_inside_lab_root(self, path: Path) -> None:
        resolved = path.resolve()
        if resolved != self.lab_root and self.lab_root not in resolved.parents:
            raise ValueError("Lab path must stay inside LAB_ROOT")
