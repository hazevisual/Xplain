from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class ProcessRecord(Base):
    __tablename__ = "processes"
    __table_args__ = (
        Index("ix_processes_updated_at", "updated_at"),
        Index("ix_processes_created_at", "created_at"),
        Index("ix_processes_status", "status"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    graph: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )


class ProcessRevisionRecord(Base):
    __tablename__ = "process_revisions"
    __table_args__ = (
        UniqueConstraint("process_id", "version", name="uq_process_revisions_process_version"),
        Index("ix_process_revisions_process_id", "process_id"),
        Index("ix_process_revisions_process_version", "process_id", "version"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    process_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("processes.id", ondelete="CASCADE"),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    graph: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )


class ProcessCommentRecord(Base):
    __tablename__ = "process_comments"
    __table_args__ = (
        Index("ix_process_comments_process_id", "process_id"),
        Index("ix_process_comments_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    process_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("processes.id", ondelete="CASCADE"),
        nullable=False,
    )
    target_type: Mapped[str] = mapped_column(String(32), nullable=False)
    target_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    message: Mapped[str] = mapped_column(Text(), nullable=False)
    author: Mapped[str] = mapped_column(String(128), nullable=False, default="reviewer")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
