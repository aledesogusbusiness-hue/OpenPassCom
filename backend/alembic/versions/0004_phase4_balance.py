"""Phase 4 — Cespiti, Ammortamenti, Chiusura esercizio

Revision ID: 0004
Revises: 0003
Create Date: 2025-01-01 03:00:00.000000

Note: FK constraints cross-table sono omesse per compatibilità
      con ambienti di migrazione incrementale. I vincoli sono
      gestiti a livello applicativo.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── fixed_assets ───────────────────────────────────────────────────────────
    op.create_table(
        "fixed_assets",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("studio_id", UUID(as_uuid=True), nullable=False),
        sa.Column("client_entity_id", UUID(as_uuid=True), nullable=False),
        sa.Column("fiscal_year_acquisto", sa.Integer, nullable=False),
        sa.Column("codice", sa.String(20), nullable=False),
        sa.Column("descrizione", sa.String(255), nullable=False),
        sa.Column("categoria", sa.String(50), nullable=False),
        sa.Column("costo_storico", sa.Numeric(15, 2), nullable=False),
        sa.Column("data_acquisto", sa.Date, nullable=False),
        sa.Column("account_id", UUID(as_uuid=True), nullable=True),
        sa.Column("aliquota_ammortamento", sa.Numeric(5, 2), nullable=False),
        sa.Column("metodo", sa.String(20), nullable=False, server_default="quote_costanti"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("note", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", UUID(as_uuid=True), nullable=True),
        sa.UniqueConstraint(
            "studio_id", "client_entity_id", "codice",
            name="uq_fixed_asset_codice",
        ),
    )
    op.create_index("ix_fixed_assets_studio_id", "fixed_assets", ["studio_id"])
    op.create_index("ix_fixed_assets_client_entity_id", "fixed_assets", ["client_entity_id"])

    # ── depreciation_entries ───────────────────────────────────────────────────
    op.create_table(
        "depreciation_entries",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("studio_id", UUID(as_uuid=True), nullable=False),
        sa.Column("fixed_asset_id", UUID(as_uuid=True), nullable=False),
        sa.Column("anno", sa.Integer, nullable=False),
        sa.Column("valore_iniziale", sa.Numeric(15, 2), nullable=False),
        sa.Column("quota_ammortamento", sa.Numeric(15, 2), nullable=False),
        sa.Column("fondo_ammortamento", sa.Numeric(15, 2), nullable=False),
        sa.Column("valore_netto_finale", sa.Numeric(15, 2), nullable=False),
        sa.Column("journal_entry_id", UUID(as_uuid=True), nullable=True),
        sa.Column("stato", sa.String(10), nullable=False, server_default="calcolato"),
        sa.UniqueConstraint("fixed_asset_id", "anno", name="uq_depreciation_asset_anno"),
    )
    op.create_index("ix_depreciation_entries_studio_id", "depreciation_entries", ["studio_id"])
    op.create_index("ix_depreciation_entries_fixed_asset_id", "depreciation_entries", ["fixed_asset_id"])

    # ── year_closings ──────────────────────────────────────────────────────────
    op.create_table(
        "year_closings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("studio_id", UUID(as_uuid=True), nullable=False),
        sa.Column("client_entity_id", UUID(as_uuid=True), nullable=False),
        sa.Column("fiscal_year_id", UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column("stato", sa.String(20), nullable=False, server_default="in_corso"),
        sa.Column("data_chiusura", sa.Date, nullable=True),
        sa.Column("note", sa.String(1000), nullable=True),
        sa.Column("totale_attivo", sa.Numeric(15, 2), nullable=True),
        sa.Column("totale_passivo", sa.Numeric(15, 2), nullable=True),
        sa.Column("totale_ricavi", sa.Numeric(15, 2), nullable=True),
        sa.Column("totale_costi", sa.Numeric(15, 2), nullable=True),
        sa.Column("utile_perdita", sa.Numeric(15, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", UUID(as_uuid=True), nullable=True),
    )
    op.create_index("ix_year_closings_studio_id", "year_closings", ["studio_id"])
    op.create_index("ix_year_closings_client_entity_id", "year_closings", ["client_entity_id"])


def downgrade() -> None:
    op.drop_table("year_closings")
    op.drop_table("depreciation_entries")
    op.drop_table("fixed_assets")
