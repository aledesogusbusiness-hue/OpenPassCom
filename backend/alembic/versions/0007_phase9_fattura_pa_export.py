"""Phase 9 — Emissione FatturaPA verso SDI (fattura_pa_exports)

Revision ID: 0007
Revises: 0006
Create Date: 2025-01-01 06:00:00.000000

Note: FK constraints cross-table sono omesse per compatibilità
      con ambienti di migrazione incrementale (e SQLite nei test).
      I vincoli sono gestiti a livello applicativo.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "fattura_pa_exports",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("studio_id", UUID(as_uuid=True), nullable=False),
        sa.Column("client_entity_id", UUID(as_uuid=True), nullable=False),
        sa.Column("fiscal_year_id", UUID(as_uuid=True), nullable=False),
        sa.Column("journal_entry_id", UUID(as_uuid=True), nullable=True),
        sa.Column("tipo_documento", sa.String(4), nullable=False, server_default="TD01"),
        sa.Column("numero_fattura", sa.String(20), nullable=False),
        sa.Column("data_fattura", sa.Date, nullable=False),
        sa.Column("cedente_indirizzo", sa.String(255), nullable=False),
        sa.Column("cedente_cap", sa.String(5), nullable=False),
        sa.Column("cedente_comune", sa.String(100), nullable=False),
        sa.Column("cedente_provincia", sa.String(2), nullable=False),
        sa.Column("destinatario_denominazione", sa.String(255), nullable=False),
        sa.Column("destinatario_partita_iva", sa.String(11), nullable=True),
        sa.Column("destinatario_codice_fiscale", sa.String(16), nullable=True),
        sa.Column("destinatario_indirizzo", sa.String(255), nullable=False),
        sa.Column("destinatario_cap", sa.String(5), nullable=False),
        sa.Column("destinatario_comune", sa.String(100), nullable=False),
        sa.Column("destinatario_provincia", sa.String(2), nullable=False),
        sa.Column("destinatario_codice_sdi", sa.String(7), nullable=False, server_default="0000000"),
        sa.Column("destinatario_pec", sa.String(255), nullable=True),
        sa.Column("xml_content", sa.Text, nullable=True),
        sa.Column("stato", sa.String(20), nullable=False, server_default="bozza"),
        sa.Column("progressivo_invio", sa.String(20), nullable=True),
        sa.Column("identificativo_sdi", sa.String(50), nullable=True),
        sa.Column("data_invio", sa.DateTime(timezone=True), nullable=True),
        sa.Column("data_esito", sa.DateTime(timezone=True), nullable=True),
        sa.Column("esito_messaggio", sa.String(1000), nullable=True),
        sa.Column("errore_msg", sa.String(500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("created_by", UUID(as_uuid=True), nullable=True),
    )
    op.create_index("ix_fattura_pa_exports_studio_id", "fattura_pa_exports", ["studio_id"])
    op.create_index(
        "ix_fattura_pa_exports_client_entity_id", "fattura_pa_exports", ["client_entity_id"]
    )
    op.create_index(
        "ix_fattura_pa_exports_fiscal_year_id", "fattura_pa_exports", ["fiscal_year_id"]
    )

    op.create_table(
        "fattura_pa_export_lines",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("studio_id", UUID(as_uuid=True), nullable=False),
        sa.Column("fattura_pa_export_id", UUID(as_uuid=True), nullable=False),
        sa.Column("numero_linea", sa.Integer, nullable=False),
        sa.Column("descrizione", sa.String(1000), nullable=False),
        sa.Column("quantita", sa.Numeric(15, 2), nullable=False, server_default="1"),
        sa.Column("unita_misura", sa.String(10), nullable=True),
        sa.Column("prezzo_unitario", sa.Numeric(15, 2), nullable=False),
        sa.Column("aliquota_iva", sa.Numeric(5, 2), nullable=False),
    )
    op.create_index("ix_fattura_pa_export_lines_studio_id", "fattura_pa_export_lines", ["studio_id"])
    op.create_index(
        "ix_fattura_pa_export_lines_fattura_pa_export_id",
        "fattura_pa_export_lines",
        ["fattura_pa_export_id"],
    )


def downgrade() -> None:
    op.drop_table("fattura_pa_export_lines")
    op.drop_table("fattura_pa_exports")
