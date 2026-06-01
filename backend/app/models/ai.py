import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AILabBuilderPreviewStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    VALID = "VALID"
    INVALID = "INVALID"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class AILabBuilderValidationStatus(str, enum.Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"


class AILabBuilderPreview(Base):
    __tablename__ = "ai_lab_builder_previews"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requested_by: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    lab_plan_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    generated_containerlab_yaml: Mapped[str] = mapped_column(Text, nullable=False)
    generated_configs: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    generated_verification_rules: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    validation_status: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    validation_errors: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_lab_template_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("lab_templates.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
