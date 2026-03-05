"""add processes timestamp indexes

Revision ID: 20260306_0002
Revises: 20260306_0001
Create Date: 2026-03-06 03:40:00
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260306_0002"
down_revision: Union[str, None] = "20260306_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("ix_processes_updated_at", "processes", ["updated_at"], unique=False)
    op.create_index("ix_processes_created_at", "processes", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_processes_created_at", table_name="processes")
    op.drop_index("ix_processes_updated_at", table_name="processes")

