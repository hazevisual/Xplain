from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from .models import ProcessRecord
from .schemas import ProcessCreateRequest, ProcessDetails, ProcessGraph, ProcessSummary, ProcessUpdateRequest


class PostgresProcessStore:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    @staticmethod
    def _to_summary(record: ProcessRecord) -> ProcessSummary:
        return ProcessSummary(
            id=record.id,
            title=record.title,
            description=record.description,
            updated_at=record.updated_at,
            version=record.version,
        )

    @staticmethod
    def _to_details(record: ProcessRecord) -> ProcessDetails:
        graph = ProcessGraph.model_validate(record.graph)
        return ProcessDetails(
            id=record.id,
            title=record.title,
            description=record.description,
            created_at=record.created_at,
            updated_at=record.updated_at,
            version=record.version,
            graph=graph,
        )

    def list(self) -> list[ProcessSummary]:
        with self._session_factory() as session:
            rows = session.scalars(select(ProcessRecord).order_by(ProcessRecord.updated_at.desc())).all()
            return [self._to_summary(row) for row in rows]

    def get(self, process_id: str) -> ProcessDetails | None:
        with self._session_factory() as session:
            row = session.get(ProcessRecord, process_id)
            if not row:
                return None
            return self._to_details(row)

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

        row = ProcessRecord(
            id=process_id,
            title=payload.title,
            description=payload.description,
            version=graph.version,
            graph=graph.model_dump(by_alias=True),
            created_at=now,
            updated_at=now,
        )

        with self._session_factory() as session:
            session.add(row)
            session.commit()
            session.refresh(row)
            return self._to_details(row)

    def update(self, process_id: str, payload: ProcessUpdateRequest) -> ProcessDetails | None:
        with self._session_factory() as session:
            row = session.get(ProcessRecord, process_id)
            if not row:
                return None

            current_graph = ProcessGraph.model_validate(row.graph)
            updated_graph = payload.graph or current_graph
            if updated_graph.process_id != process_id:
                updated_graph = updated_graph.model_copy(update={"process_id": process_id})

            row.title = payload.title if payload.title is not None else row.title
            row.description = payload.description if payload.description is not None else row.description
            row.graph = updated_graph.model_dump(by_alias=True)
            row.version = updated_graph.version
            row.updated_at = datetime.now(UTC)

            session.add(row)
            session.commit()
            session.refresh(row)
            return self._to_details(row)

    def delete(self, process_id: str) -> bool:
        with self._session_factory() as session:
            row = session.get(ProcessRecord, process_id)
            if not row:
                return False
            session.delete(row)
            session.commit()
            return True

