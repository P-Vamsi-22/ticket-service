"""Day 12: login + roles (users.password_hash, users.role)

Revision ID: 0002_auth
Revises: 0001_initial
Create Date: 2026-11-27
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_auth"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch:
        batch.add_column(sa.Column("password_hash", sa.String(length=255), nullable=True))
        batch.add_column(
            sa.Column("role", sa.String(length=20), nullable=False, server_default="EMPLOYEE")
        )


def downgrade() -> None:
    with op.batch_alter_table("users") as batch:
        batch.drop_column("role")
        batch.drop_column("password_hash")
