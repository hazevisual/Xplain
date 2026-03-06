"""add process comments table

Revision ID: 20260306_0005
Revises: 20260306_0004
Create Date: 2026-03-06 05:55:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260306_0005"
down_revision: Union[str, None] = "20260306_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "process_comments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("process_id", sa.String(length=64), nullable=False),
        sa.Column("target_type", sa.String(length=32), nullable=False),
        sa.Column("target_id", sa.String(length=128), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("author", sa.String(length=128), nullable=False, server_default="reviewer"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["process_id"], ["processes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_process_comments_process_id", "process_comments", ["process_id"], unique=False)
    op.create_index("ix_process_comments_created_at", "process_comments", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_process_comments_created_at", table_name="process_comments")
    op.drop_index("ix_process_comments_process_id", table_name="process_comments")
    op.drop_table("process_comments")

