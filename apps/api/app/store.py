from __future__ import annotations

from datetime import UTC, datetime
from threading import Lock
from typing import Protocol
from uuid import uuid4

from .schemas import ProcessCreateRequest, ProcessDetails, ProcessGraph, ProcessSummary, ProcessUpdateRequest


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


class InMemoryProcessStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self._data: dict[str, ProcessDetails] = {}

    def list(self) -> list[ProcessSummary]:
        with self._lock:
            return [
                ProcessSummary(
                    id=item.id,
                    title=item.title,
                    description=item.description,
                    updated_at=item.updated_at,
                    version=item.version,
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
            graph=graph,
        )

        with self._lock:
            self._data[process_id] = item

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
            return updated.model_copy(deep=True)

    def delete(self, process_id: str) -> bool:
        with self._lock:
            if process_id not in self._data:
                return False
            del self._data[process_id]
            return True
