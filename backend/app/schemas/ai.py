import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


NodeKind = Literal["linux", "frr"]
LabCategory = Literal["Linux", "BGP", "OSPF"]
LabDifficulty = Literal["Easy", "Medium", "Hard"]
ParserType = Literal["SIMPLE_TEXT"]
AssertionType = Literal[
    "CONTAINS",
    "NOT_CONTAINS",
    "EQUALS",
    "EXIT_CODE_ZERO",
    "BGP_NEIGHBOR_ESTABLISHED",
    "ROUTE_EXISTS",
]


class AILabBuilderPreviewCreate(BaseModel):
    prompt: str = Field(min_length=10, max_length=5000)


class LabPlanNode(BaseModel):
    name: str = Field(min_length=1, max_length=63)
    kind: NodeKind
    role: str = Field(min_length=1, max_length=60)
    image: str = Field(min_length=1, max_length=180)


class LabPlanLink(BaseModel):
    endpoints: list[str] = Field(min_length=2, max_length=2)
    subnet: str | None = Field(default=None, max_length=64)


class LabPlanAddress(BaseModel):
    node: str = Field(min_length=1, max_length=63)
    interface: str = Field(min_length=1, max_length=40)
    ipv4: str = Field(min_length=1, max_length=64)


class LabPlanStaticRoute(BaseModel):
    node: str = Field(min_length=1, max_length=63)
    prefix: str = Field(min_length=1, max_length=64)
    next_hop: str = Field(min_length=1, max_length=64)


class LabPlanOspf(BaseModel):
    enabled: bool = False
    area: str = Field(default="0", max_length=32)
    nodes: list[str] = Field(default_factory=list, max_length=6)


class LabPlanBgpSession(BaseModel):
    local_node: str = Field(min_length=1, max_length=63)
    local_as: int = Field(ge=1, le=4294967295)
    peer_node: str = Field(min_length=1, max_length=63)
    peer_as: int = Field(ge=1, le=4294967295)


class LabPlanBgp(BaseModel):
    enabled: bool = False
    sessions: list[LabPlanBgpSession] = Field(default_factory=list, max_length=10)


class LabPlanProtocols(BaseModel):
    static_routes: list[LabPlanStaticRoute] = Field(default_factory=list, max_length=20)
    ospf: LabPlanOspf = Field(default_factory=LabPlanOspf)
    bgp: LabPlanBgp = Field(default_factory=LabPlanBgp)


class LabPlanStartupConfig(BaseModel):
    node: str = Field(min_length=1, max_length=63)
    config_type: Literal["frr", "linux", "none"] = "none"
    content: str = Field(default="", max_length=20000)


class LabPlanVerificationRule(BaseModel):
    name: str = Field(min_length=3, max_length=180)
    target_node: str = Field(min_length=1, max_length=120)
    command: str = Field(min_length=1, max_length=500)
    parser_type: ParserType = "SIMPLE_TEXT"
    assertion_type: AssertionType
    expected_value: str | None = Field(default=None, max_length=5000)
    timeout_seconds: int = Field(default=10, ge=1, le=60)
    is_active: bool = True


class LabPlan(BaseModel):
    lab_name: str = Field(min_length=3, max_length=80)
    title: str = Field(min_length=3, max_length=150)
    description: str = Field(min_length=1, max_length=5000)
    category: LabCategory
    difficulty: LabDifficulty
    estimated_cpu: int = Field(ge=1, le=64)
    estimated_memory_mb: int = Field(ge=128, le=131072)
    estimated_duration_minutes: int = Field(ge=1, le=1440)
    nodes: list[LabPlanNode] = Field(min_length=1, max_length=6)
    links: list[LabPlanLink] = Field(default_factory=list, max_length=10)
    addressing: list[LabPlanAddress] = Field(default_factory=list, max_length=20)
    protocols: LabPlanProtocols = Field(default_factory=LabPlanProtocols)
    startup_configs: list[LabPlanStartupConfig] = Field(default_factory=list, max_length=6)
    verification_rules: list[LabPlanVerificationRule] = Field(default_factory=list, max_length=10)
    student_instructions: str = Field(min_length=1, max_length=20000)
    hints: str | None = Field(default=None, max_length=20000)
    safety_notes: list[str] = Field(default_factory=list, max_length=20)


class AILabBuilderPreviewRead(BaseModel):
    id: uuid.UUID
    requested_by: uuid.UUID
    prompt: str
    lab_plan_json: dict
    generated_containerlab_yaml: str
    generated_configs: list[dict]
    generated_verification_rules: list[dict]
    validation_status: str
    validation_errors: list[str]
    status: str
    approved_at: datetime | None
    approved_by: uuid.UUID | None
    created_lab_template_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AILabBuilderApprovalRead(BaseModel):
    preview: AILabBuilderPreviewRead
    created_lab_template_id: uuid.UUID
