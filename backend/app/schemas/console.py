import uuid

from pydantic import BaseModel, Field


class ConsoleNodeRead(BaseModel):
    id: uuid.UUID
    name: str
    kind: str
    status: str
    management_ipv4: str | None
    console_type: str


class ConsoleNodesRead(BaseModel):
    nodes: list[ConsoleNodeRead]


class ConsoleExecuteRequest(BaseModel):
    command: str = Field(min_length=1, max_length=300)


class ConsoleBatchRequest(BaseModel):
    commands: list[str] = Field(min_length=1, max_length=20)


class ConsoleExecuteRead(BaseModel):
    status: str
    command: str
    stdout: str
    stderr: str
    exit_code: int
    duration_ms: int
