"""Phase 8 — Permessi granulari per cliente (client_user_permissions)

Revision ID: 0006
Revises: 0005
Create Date: 2025-01-01 05:00:00.000000

Note: FK constraints cross-table sono omesse per compatibilità
      con ambienti di migrazione incrementale (e SQLite nei test).
      I vincoli sono gestiti a livello applicativo.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "client_user_permissions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("studio_id", UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("client_entity_id", UUID(as_uuid=True), nullable=False),
        sa.Column("permesso", sa.String(10), nullable=False, server_default="lettura"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("created_by", UUID(as_uuid=True), nullable=True),
        sa.UniqueConstraint("user_id", "client_entity_id", name="uq_client_user_permission"),
    )
    op.create_index(
        "ix_client_user_permissions_studio_id", "client_user_permissions", ["studio_id"]
    )
    op.create_index(
        "ix_client_user_permissions_user_id", "client_user_permissions", ["user_id"]
    )
    op.create_index(
        "ix_client_user_permissions_client_entity_id",
        "client_user_permissions",
        ["client_entity_id"],
    )


def downgrade() -> None:
    op.drop_table("client_user_permissions")
