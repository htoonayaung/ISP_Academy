import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.lab_instance import LabEventRead


class RuntimeContainerSummary(BaseModel):
    source: str
    known_container_count: int
    running_lab_count: int
    message: str


class RuntimeLabSummary(BaseModel):
    id: uuid.UUID
    lab_name: str
    owner_id: uuid.UUID
    status: str
    created_at: datetime
    updated_at: datetime
    is_demo: bool
    has_containers: bool
    warning: str | None = None


class RuntimeOrphanCandidate(BaseModel):
    path: str
    warning: str


class RuntimeStatusRead(BaseModel):
    containers: RuntimeContainerSummary
    status_counts: dict[str, int]
    labs_by_status: dict[str, list[RuntimeLabSummary]]
    stuck_candidates: list[RuntimeLabSummary]
    orphan_candidates: list[RuntimeOrphanCandidate]
    demo_labs: list[RuntimeLabSummary]
    warnings: list[str]


class RuntimeRefreshRead(BaseModel):
    queued_refresh_count: int
    inspected_statuses: list[str]
    warnings: list[str]


class RuntimeRecoverRequest(BaseModel):
    action: Literal["mark_failed", "retry_destroy", "force_destroy_demo_only"]
    confirm: str = Field(min_length=1)


class RuntimeRecoverRead(BaseModel):
    lab_id: uuid.UUID
    action: str
    status: str
    queued_task: bool
    message: str


class RuntimeCleanupRequest(BaseModel):
    confirm: str = Field(min_length=1)


class RuntimeCleanupRead(BaseModel):
    queued_task: bool
    eligible_demo_labs: list[RuntimeLabSummary]
    skipped: list[str]
    message: str


class RuntimeEventsRead(BaseModel):
    lab_id: uuid.UUID
    events: list[LabEventRead]
