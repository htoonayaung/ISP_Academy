import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ParserTypeValue(str, Enum):
    SIMPLE_TEXT = "SIMPLE_TEXT"
    JSON_FUTURE = "JSON_FUTURE"
    TEXTFSM_FUTURE = "TEXTFSM_FUTURE"
    GENIE_FUTURE = "GENIE_FUTURE"


class AssertionTypeValue(str, Enum):
    CONTAINS = "CONTAINS"
    NOT_CONTAINS = "NOT_CONTAINS"
    EQUALS = "EQUALS"
    EXIT_CODE_ZERO = "EXIT_CODE_ZERO"
    BGP_NEIGHBOR_ESTABLISHED = "BGP_NEIGHBOR_ESTABLISHED"
    ROUTE_EXISTS = "ROUTE_EXISTS"


class VerificationRuleCreate(BaseModel):
    name: str = Field(min_length=3, max_length=180)
    target_node: str = Field(min_length=1, max_length=120)
    command: str = Field(min_length=1, max_length=500)
    parser_type: ParserTypeValue = ParserTypeValue.SIMPLE_TEXT
    assertion_type: AssertionTypeValue
    expected_value: str | None = Field(default=None, max_length=5000)
    timeout_seconds: int = Field(default=10, ge=1, le=60)
    is_active: bool = True


class VerificationRuleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=3, max_length=180)
    target_node: str | None = Field(default=None, min_length=1, max_length=120)
    command: str | None = Field(default=None, min_length=1, max_length=500)
    parser_type: ParserTypeValue | None = None
    assertion_type: AssertionTypeValue | None = None
    expected_value: str | None = Field(default=None, max_length=5000)
    timeout_seconds: int | None = Field(default=None, ge=1, le=60)
    is_active: bool | None = None


class VerificationRuleRead(BaseModel):
    id: uuid.UUID
    ticket_id: uuid.UUID
    name: str
    target_node: str
    command: str
    parser_type: str
    assertion_type: str
    expected_value: str | None
    timeout_seconds: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VerificationResultRead(BaseModel):
    id: uuid.UUID
    verification_run_id: uuid.UUID
    verification_rule_id: uuid.UUID
    status: str
    actual_output: str | None
    message: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VerificationRunRead(BaseModel):
    id: uuid.UUID
    ticket_attempt_id: uuid.UUID
    status: str
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
    results: list[VerificationResultRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
