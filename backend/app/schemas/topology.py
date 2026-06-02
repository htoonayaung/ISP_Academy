from typing import Any

from pydantic import BaseModel, Field


class TopologyNode(BaseModel):
    id: str
    label: str
    kind: str
    role: str | None = None
    image: str | None = None
    status: str | None = None
    management_ipv4: str | None = None
    container_name: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class TopologyLink(BaseModel):
    id: str
    source: str
    target: str
    source_interface: str | None = None
    target_interface: str | None = None
    label: str
    subnet: str | None = None


class TopologyRead(BaseModel):
    nodes: list[TopologyNode]
    links: list[TopologyLink]
    warnings: list[str] = Field(default_factory=list)
