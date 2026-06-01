import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class TicketStatusValue(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class TicketAttemptStatusValue(str, Enum):
    STARTED = "STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    PASSED = "PASSED"
    FAILED = "FAILED"


class TicketCreate(BaseModel):
    lab_template_id: uuid.UUID
    title: str = Field(min_length=3, max_length=180)
    description: str = Field(min_length=1, max_length=5000)
    student_instructions: str = Field(min_length=1, max_length=20000)
    hints: str | None = Field(default=None, max_length=20000)
    hidden_solution: str | None = Field(default=None, max_length=50000)
    status: TicketStatusValue = TicketStatusValue.DRAFT


class TicketUpdate(BaseModel):
    lab_template_id: uuid.UUID | None = None
    title: str | None = Field(default=None, min_length=3, max_length=180)
    description: str | None = Field(default=None, min_length=1, max_length=5000)
    student_instructions: str | None = Field(default=None, min_length=1, max_length=20000)
    hints: str | None = Field(default=None, max_length=20000)
    hidden_solution: str | None = Field(default=None, max_length=50000)
    status: TicketStatusValue | None = None


class TicketStudentRead(BaseModel):
    id: uuid.UUID
    lab_template_id: uuid.UUID
    title: str
    slug: str
    description: str
    student_instructions: str
    hints: str | None
    status: str
    created_by: uuid.UUID
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TicketPrivateRead(TicketStudentRead):
    hidden_solution: str | None


class TicketAttemptRead(BaseModel):
    id: uuid.UUID
    ticket_id: uuid.UUID
    student_id: uuid.UUID
    lab_instance_id: uuid.UUID
    status: str
    started_at: datetime
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
