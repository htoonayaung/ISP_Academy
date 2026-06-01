import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class LabTemplateCategory(str, Enum):
    LINUX = "Linux"
    BGP = "BGP"
    OSPF = "OSPF"
    ISIS = "ISIS"
    MPLS = "MPLS"
    EVPN = "EVPN"
    VXLAN = "VXLAN"
    SECURITY = "Security"


class LabTemplateDifficulty(str, Enum):
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"


class LabTemplateCreate(BaseModel):
    name: str = Field(min_length=3, max_length=150)
    description: str = Field(min_length=1, max_length=5000)
    category: LabTemplateCategory
    difficulty: LabTemplateDifficulty
    containerlab_yaml: str = Field(min_length=1, max_length=200_000)
    default_startup_config: str | None = Field(default=None, max_length=200_000)
    estimated_cpu: int = Field(ge=1, le=64)
    estimated_memory_mb: int = Field(ge=128, le=131_072)
    estimated_duration_minutes: int = Field(ge=1, le=1440)
    is_active: bool = False


class LabTemplateUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=3, max_length=150)
    description: str | None = Field(default=None, min_length=1, max_length=5000)
    category: LabTemplateCategory | None = None
    difficulty: LabTemplateDifficulty | None = None
    containerlab_yaml: str | None = Field(default=None, min_length=1, max_length=200_000)
    default_startup_config: str | None = Field(default=None, max_length=200_000)
    estimated_cpu: int | None = Field(default=None, ge=1, le=64)
    estimated_memory_mb: int | None = Field(default=None, ge=128, le=131_072)
    estimated_duration_minutes: int | None = Field(default=None, ge=1, le=1440)
    is_active: bool | None = None


class LabTemplateRead(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    description: str
    category: str
    difficulty: str
    containerlab_yaml: str
    default_startup_config: str | None
    estimated_cpu: int
    estimated_memory_mb: int
    estimated_duration_minutes: int
    is_active: bool
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LabTemplateValidationResult(BaseModel):
    is_valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

