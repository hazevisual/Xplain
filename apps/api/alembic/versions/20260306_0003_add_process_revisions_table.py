"""add process revisions table

Revision ID: 20260306_0003
Revises: 20260306_0002
Create Date: 2026-03-06 05:10:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260306_0003"
down_revision: Union[str, None] = "20260306_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "process_revisions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("process_id", sa.String(length=64), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("graph", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["process_id"], ["processes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("process_id", "version", name="uq_process_revisions_process_version"),
    )
    op.create_index("ix_process_revisions_process_id", "process_revisions", ["process_id"], unique=False)
    op.create_index(
        "ix_process_revisions_process_version",
        "process_revisions",
        ["process_id", "version"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_process_revisions_process_version", table_name="process_revisions")
    op.drop_index("ix_process_revisions_process_id", table_name="process_revisions")
    op.drop_table("process_revisions")

