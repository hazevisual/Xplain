from __future__ import annotations

from datetime import UTC, datetime
from threading import Lock
from typing import Protocol
from uuid import uuid4

from .schemas import (
    ProcessCreateRequest,
    ProcessDetails,
    ProcessGraph,
    ProcessRevisionSummary,
    ProcessStatus,
    ProcessSummary,
    ProcessUpdateRequest,
)

ALLOWED_STATUS_TRANSITIONS: dict[ProcessStatus, set[ProcessStatus]] = {
    ProcessStatus.draft: {ProcessStatus.in_review},
    ProcessStatus.in_review: {ProcessStatus.approved},
    ProcessStatus.approved: set(),
}


class ProcessStore(Protocol):
    def list(self) -> list[ProcessSummary]:
        ...

    def get(self, process_id: str) -> ProcessDetails | None:
        ...

    def create(self, payload: ProcessCreateRequest) -> ProcessDetails:
        ...

    def update(self, process_id: str, payload: ProcessUpdateRequest) -> ProcessDetails | None:
        ...

    def delete(self, process_id: str) -> bool:
        ...

    def list_revisions(self, process_id: str) -> list[ProcessRevisionSummary]:
        ...

    def transition_status(self, process_id: str, target_status: ProcessStatus) -> ProcessDetails | None:
        ...


class InMemoryProcessStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self._data: dict[str, ProcessDetails] = {}
        self._revisions: dict[str, dict[int, ProcessDetails]] = {}

    @staticmethod
    def _to_revision_summary(item: ProcessDetails) -> ProcessRevisionSummary:
        return ProcessRevisionSummary(
            version=item.version,
            created_at=item.updated_at,
            nodes_count=len(item.graph.nodes),
            edges_count=len(item.graph.edges),
            warnings_count=len(item.graph.warnings),
            coverage_percent=item.graph.quality.coverage_percent,
        )

    def list(self) -> list[ProcessSummary]:
        with self._lock:
            return [
                ProcessSummary(
                    id=item.id,
                    title=item.title,
                    description=item.description,
                    updated_at=item.updated_at,
                    version=item.version,
                    status=item.status,
                )
                for item in sorted(self._data.values(), key=lambda i: i.updated_at, reverse=True)
            ]

    def get(self, process_id: str) -> ProcessDetails | None:
        with self._lock:
            item = self._data.get(process_id)
            return item.model_copy(deep=True) if item else None

    def create(self, payload: ProcessCreateRequest) -> ProcessDetails:
        now = datetime.now(UTC)
        process_id = uuid4().hex
        graph = payload.graph or ProcessGraph(
            processId=process_id,
            version=1,
            nodes=[],
            edges=[],
            warnings=[],
            sourceRefs=[],
        )

        if graph.process_id != process_id:
            graph = graph.model_copy(update={"process_id": process_id})

        item = ProcessDetails(
            id=process_id,
            title=payload.title,
            description=payload.description,
            created_at=now,
            updated_at=now,
            version=graph.version,
            status=ProcessStatus.draft,
            graph=graph,
        )

        with self._lock:
            self._data[process_id] = item
            self._revisions[process_id] = {item.version: item.model_copy(deep=True)}

        return item.model_copy(deep=True)

    def update(self, process_id: str, payload: ProcessUpdateRequest) -> ProcessDetails | None:
        with self._lock:
            existing = self._data.get(process_id)
            if not existing:
                return None

            updated_graph = payload.graph or existing.graph
            if updated_graph.process_id != process_id:
                updated_graph = updated_graph.model_copy(update={"process_id": process_id})

            updated = existing.model_copy(
                update={
                    "title": payload.title if payload.title is not None else existing.title,
                    "description": payload.description if payload.description is not None else existing.description,
                    "graph": updated_graph,
                    "version": updated_graph.version,
                    "updated_at": datetime.now(UTC),
                },
                deep=True,
            )
            self._data[process_id] = updated
            if process_id not in self._revisions:
                self._revisions[process_id] = {}
            self._revisions[process_id][updated.version] = updated.model_copy(deep=True)
            return updated.model_copy(deep=True)

    def delete(self, process_id: str) -> bool:
        with self._lock:
            if process_id not in self._data:
                return False
            del self._data[process_id]
            if process_id in self._revisions:
                del self._revisions[process_id]
            return True

    def list_revisions(self, process_id: str) -> list[ProcessRevisionSummary]:
        with self._lock:
            versions = self._revisions.get(process_id, {})
            snapshots = [versions[v] for v in sorted(versions.keys(), reverse=True)]
            return [self._to_revision_summary(item) for item in snapshots]

    def transition_status(self, process_id: str, target_status: ProcessStatus) -> ProcessDetails | None:
        with self._lock:
            existing = self._data.get(process_id)
            if not existing:
                return None

            current_status = existing.status
            allowed = ALLOWED_STATUS_TRANSITIONS[current_status]
            if target_status not in allowed and target_status != current_status:
                raise ValueError(f"Invalid transition: {current_status} -> {target_status}")

            updated = existing.model_copy(
                update={"status": target_status, "updated_at": datetime.now(UTC)},
                deep=True,
            )
            self._data[process_id] = updated
            return updated.model_copy(deep=True)
