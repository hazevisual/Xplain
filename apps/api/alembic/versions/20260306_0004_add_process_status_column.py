"""add process status column

Revision ID: 20260306_0004
Revises: 20260306_0003
Create Date: 2026-03-06 05:30:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260306_0004"
down_revision: Union[str, None] = "20260306_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("processes", sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"))
    op.create_index("ix_processes_status", "processes", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_processes_status", table_name="processes")
    op.drop_column("processes", "status")

