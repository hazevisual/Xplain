from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


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


class ProcessStatus(str, Enum):
    draft = "draft"
    in_review = "in_review"
    approved = "approved"


class CommentTargetType(str, Enum):
    process = "process"
    node = "node"
    edge = "edge"


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


class GraphQuality(BaseModel):
    coverage_percent: float = Field(default=0.0, ge=0, le=100)
    dangling_nodes: list[str] = Field(default_factory=list)
    naming_consistency_percent: float = Field(default=0.0, ge=0, le=100)


class ProcessGraph(BaseModel):
    process_id: str = Field(alias="processId", min_length=1)
    version: int = Field(ge=1)
    nodes: list[ProcessNode] = Field(default_factory=list)
    edges: list[ProcessEdge] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(alias="sourceRefs", default_factory=list)
    quality: GraphQuality = Field(default_factory=GraphQuality)

    model_config = {"populate_by_name": True}


class ProcessCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=20_000)
    graph: ProcessGraph | None = None

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str) -> str:
        title = value.strip()
        if not title:
            raise ValueError("Title must not be empty")
        return title

    @field_validator("description", mode="before")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        if not isinstance(value, str):
            return value
        cleaned = value.strip()
        return cleaned or None


class ProcessUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=20_000)
    graph: ProcessGraph | None = None

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        title = value.strip()
        if not title:
            raise ValueError("Title must not be empty")
        return title

    @field_validator("description", mode="before")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        if not isinstance(value, str):
            return value
        return value.strip()


class GenerateGraphRequest(BaseModel):
    text: str | None = Field(default=None, max_length=20_000)

    @field_validator("text", mode="before")
    @classmethod
    def normalize_text(cls, value: str | None) -> str | None:
        if not isinstance(value, str):
            return value
        return value.strip()


class ProcessStatusTransitionRequest(BaseModel):
    target_status: ProcessStatus = Field(alias="targetStatus")

    model_config = {"populate_by_name": True}


class ProcessCommentCreateRequest(BaseModel):
    target_type: CommentTargetType = Field(alias="targetType")
    target_id: str | None = Field(default=None, alias="targetId", min_length=1, max_length=128)
    message: str = Field(min_length=1, max_length=2000)
    author: str | None = Field(default=None, max_length=128)

    model_config = {"populate_by_name": True}

    @field_validator("message")
    @classmethod
    def normalize_message(cls, value: str) -> str:
        message = value.strip()
        if not message:
            raise ValueError("Message must not be empty")
        return message

    @field_validator("author", mode="before")
    @classmethod
    def normalize_author(cls, value: str | None) -> str | None:
        if not isinstance(value, str):
            return value
        cleaned = value.strip()
        return cleaned or None

    @model_validator(mode="after")
    def validate_target(self) -> "ProcessCommentCreateRequest":
        if self.target_type == CommentTargetType.process:
            self.target_id = None
            return self
        if not self.target_id:
            raise ValueError("targetId is required for node/edge comments")
        return self


class ErrorPayload(BaseModel):
    code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    details: Any | None = None


class ErrorResponse(BaseModel):
    error: ErrorPayload


class ProcessSummary(BaseModel):
    id: str
    title: str
    description: str | None = None
    updated_at: datetime
    version: int
    status: ProcessStatus


class ProcessRevisionSummary(BaseModel):
    version: int
    created_at: datetime
    nodes_count: int
    edges_count: int
    warnings_count: int
    coverage_percent: float = Field(ge=0, le=100)


class ProcessComment(BaseModel):
    id: int
    process_id: str = Field(alias="processId")
    target_type: CommentTargetType = Field(alias="targetType")
    target_id: str | None = Field(default=None, alias="targetId")
    message: str
    author: str
    created_at: datetime = Field(alias="createdAt")

    model_config = {"populate_by_name": True}


class NarrativeStep(BaseModel):
    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    detail: str = Field(min_length=1)


class NarrativeDependency(BaseModel):
    from_node_id: str = Field(alias="fromNodeId", min_length=1)
    from_title: str = Field(alias="fromTitle", min_length=1)
    to_node_id: str = Field(alias="toNodeId", min_length=1)
    to_title: str = Field(alias="toTitle", min_length=1)
    relation: EdgeKind

    model_config = {"populate_by_name": True}


class NarrativeReference(BaseModel):
    label: str = Field(min_length=1)
    ref: str = Field(min_length=1)


class ProcessNarrative(BaseModel):
    process_id: str = Field(alias="processId", min_length=1)
    version: int = Field(ge=1)
    summary: str = Field(min_length=1)
    steps: list[NarrativeStep] = Field(default_factory=list)
    key_dependencies: list[NarrativeDependency] = Field(alias="keyDependencies", default_factory=list)
    references: list[NarrativeReference] = Field(default_factory=list)
    quality_notes: list[str] = Field(alias="qualityNotes", default_factory=list)
    source_refs: list[str] = Field(alias="sourceRefs", default_factory=list)
    generated_by: str = Field(alias="generatedBy", min_length=1)

    model_config = {"populate_by_name": True}


class ProcessDetails(ProcessSummary):
    created_at: datetime
    graph: ProcessGraph
