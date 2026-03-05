from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class NodeType(str, Enum):
    stage = "stage"
    subprocess = "subprocess"
    component = "component"
    data = "data"
    actor = "actor"


class NodeLevel(str, Enum):
    l1 = "L1"
    l2 = "L2"
    l3 = "L3"


class EdgeKind(str, Enum):
    flow = "flow"
    depends_on = "depends_on"
    uses = "uses"
    produces = "produces"


class ProcessNode(BaseModel):
    id: str = Field(min_length=1)
    type: NodeType
    title: str = Field(min_length=1)
    level: NodeLevel
    meta: dict[str, Any] = Field(default_factory=dict)


class ProcessEdge(BaseModel):
    id: str = Field(min_length=1)
    from_node: str = Field(alias="from", min_length=1)
    to: str = Field(min_length=1)
    kind: EdgeKind
    meta: dict[str, Any] = Field(default_factory=dict)

    model_config = {"populate_by_name": True}


class ProcessGraph(BaseModel):
    process_id: str = Field(alias="processId", min_length=1)
    version: int = Field(ge=1)
    nodes: list[ProcessNode] = Field(default_factory=list)
    edges: list[ProcessEdge] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(alias="sourceRefs", default_factory=list)

    model_config = {"populate_by_name": True}


class ProcessCreateRequest(BaseModel):
    title: str = Field(min_length=1)
    description: str | None = None
    graph: ProcessGraph | None = None


class ProcessUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1)
    description: str | None = None
    graph: ProcessGraph | None = None


class GenerateGraphRequest(BaseModel):
    text: str | None = None


class ProcessSummary(BaseModel):
    id: str
    title: str
    description: str | None = None
    updated_at: datetime
    version: int


class ProcessDetails(ProcessSummary):
    created_at: datetime
    graph: ProcessGraph
