"""add note color column

Revision ID: 3a4f1c8d9e21
Revises: 7d7e06f48cf7
Create Date: 2026-05-07 00:00:00.000000+00:00
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "3a4f1c8d9e21"
down_revision: Union[str, None] = "7d7e06f48cf7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("notes", sa.Column("color", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("notes", "color")
