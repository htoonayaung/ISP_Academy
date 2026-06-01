import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict


class LabStatus(str, Enum):
    CREATED = "CREATED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    DESTROYING = "DESTROYING"
    DESTROYED = "DESTROYED"
    FAILED = "FAILED"


class LabCreate(BaseModel):
    template_id: uuid.UUID


class LabRead(BaseModel):
    id: uuid.UUID
    template_id: uuid.UUID
    owner_id: uuid.UUID
    status: str
    lab_name: str
    lab_directory: str
    started_at: datetime | None
    stopped_at: datetime | None
    destroyed_at: datetime | None
    last_error: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LabStatusRead(BaseModel):
    id: uuid.UUID
    status: str
    last_error: str | None


class LabNodeRead(BaseModel):
    id: uuid.UUID
    lab_instance_id: uuid.UUID
    name: str
    kind: str
    role: str | None
    container_name: str | None
    management_ipv4: str | None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LabEventRead(BaseModel):
    id: uuid.UUID
    lab_instance_id: uuid.UUID
    event_type: str
    message: str
    stdout: str | None
    stderr: str | None
    created_by: uuid.UUID | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
