"""Phase 3 — Liquidazione IVA, Ritenute, FatturaPA Import

Revision ID: 0003
Revises: 0002
Create Date: 2025-01-01 02:00:00.000000

Note: FK constraints verso tabelle di altre fasi sono omesse per compatibilità
      con ambienti di migrazione incrementale. I vincoli di integrità sono
      gestiti a livello applicativo.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── vat_settlements ────────────────────────────────────────────────────────
    op.create_table(
        "vat_settlements",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("studio_id", UUID(as_uuid=True), nullable=False),
        sa.Column("client_entity_id", UUID(as_uuid=True), nullable=False),
        sa.Column("fiscal_year_id", UUID(as_uuid=True), nullable=False),
        sa.Column("periodo", sa.String(10), nullable=False),
        sa.Column("tipo_periodo", sa.String(10), nullable=False),
        sa.Column("iva_vendite", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("iva_acquisti", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("credito_precedente", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("debito_versare", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("credito_periodo", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("stato", sa.String(10), nullable=False, server_default="bozza"),
        sa.Column("data_versamento", sa.Date, nullable=True),
        sa.Column("f24_riferimento", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", UUID(as_uuid=True), nullable=True),
        sa.UniqueConstraint(
            "studio_id", "client_entity_id", "fiscal_year_id", "periodo",
            name="uq_vat_settlement_periodo",
        ),
    )
    op.create_index("ix_vat_settlements_studio_id", "vat_settlements", ["studio_id"])
    op.create_index("ix_vat_settlements_client_entity_id", "vat_settlements", ["client_entity_id"])
    op.create_index("ix_vat_settlements_fiscal_year_id", "vat_settlements", ["fiscal_year_id"])

    # ── withholding_taxes ──────────────────────────────────────────────────────
    op.create_table(
        "withholding_taxes",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("studio_id", UUID(as_uuid=True), nullable=False),
        sa.Column("client_entity_id", UUID(as_uuid=True), nullable=False),
        sa.Column("fiscal_year_id", UUID(as_uuid=True), nullable=False),
        sa.Column("journal_entry_id", UUID(as_uuid=True), nullable=True),
        sa.Column("tipo", sa.String(20), nullable=False),
        sa.Column("codice_tributo", sa.String(10), nullable=False, server_default="1040"),
        sa.Column("imponibile", sa.Numeric(15, 2), nullable=False),
        sa.Column("aliquota_pct", sa.Numeric(5, 2), nullable=False),
        sa.Column("importo_ritenuta", sa.Numeric(15, 2), nullable=False),
        sa.Column("mese_competenza", sa.Integer, nullable=False),
        sa.Column("anno_competenza", sa.Integer, nullable=False),
        sa.Column("stato", sa.String(10), nullable=False, server_default="da_versare"),
        sa.Column("data_versamento", sa.Date, nullable=True),
        sa.Column("f24_riferimento", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_withholding_taxes_studio_id", "withholding_taxes", ["studio_id"])
    op.create_index("ix_withholding_taxes_client_entity_id", "withholding_taxes", ["client_entity_id"])
    op.create_index("ix_withholding_taxes_fiscal_year_id", "withholding_taxes", ["fiscal_year_id"])

    # ── fattura_pa_imports ─────────────────────────────────────────────────────
    op.create_table(
        "fattura_pa_imports",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("studio_id", UUID(as_uuid=True), nullable=False),
        sa.Column("client_entity_id", UUID(as_uuid=True), nullable=False),
        sa.Column("fiscal_year_id", UUID(as_uuid=True), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("xml_content", sa.Text, nullable=False),
        sa.Column("parsed_data", sa.JSON, nullable=True),
        sa.Column("stato", sa.String(20), nullable=False, server_default="importata"),
        sa.Column("journal_entry_id", UUID(as_uuid=True), nullable=True),
        sa.Column("errore_msg", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_fattura_pa_imports_studio_id", "fattura_pa_imports", ["studio_id"])
    op.create_index("ix_fattura_pa_imports_client_entity_id", "fattura_pa_imports", ["client_entity_id"])
    op.create_index("ix_fattura_pa_imports_fiscal_year_id", "fattura_pa_imports", ["fiscal_year_id"])


def downgrade() -> None:
    op.drop_table("fattura_pa_imports")
    op.drop_table("withholding_taxes")
    op.drop_table("vat_settlements")
