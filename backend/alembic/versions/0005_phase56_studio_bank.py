"""Phase 5+6 — Studio Tasks, Riconciliazione bancaria, Conservatore

Revision ID: 0005
Revises: 0004
Create Date: 2025-01-01 04:00:00.000000

Note: FK constraints cross-table sono omesse per compatibilità
      con ambienti di migrazione incrementale (e SQLite nei test).
      I vincoli sono gestiti a livello applicativo.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── studio_tasks ───────────────────────────────────────────────────────────
    op.create_table(
        "studio_tasks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("studio_id", UUID(as_uuid=True), nullable=False),
        sa.Column("client_entity_id", UUID(as_uuid=True), nullable=True),
        sa.Column("fiscal_year_id", UUID(as_uuid=True), nullable=True),
        sa.Column("titolo", sa.String(255), nullable=False),
        sa.Column("descrizione", sa.String(2000), nullable=True),
        sa.Column("tipo", sa.String(30), nullable=False),
        sa.Column("priorita", sa.String(10), nullable=False, server_default="normale"),
        sa.Column("stato", sa.String(10), nullable=False, server_default="aperto"),
        sa.Column("data_scadenza", sa.Date, nullable=True),
        sa.Column("assegnato_a", UUID(as_uuid=True), nullable=True),
        sa.Column("completato_il", sa.Date, nullable=True),
        sa.Column("note", sa.String(1000), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("created_by", UUID(as_uuid=True), nullable=True),
    )
    op.create_index("ix_studio_tasks_studio_id", "studio_tasks", ["studio_id"])
    op.create_index("ix_studio_tasks_client_entity_id", "studio_tasks", ["client_entity_id"])

    # ── bank_statements ────────────────────────────────────────────────────────
    op.create_table(
        "bank_statements",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("studio_id", UUID(as_uuid=True), nullable=False),
        sa.Column("client_entity_id", UUID(as_uuid=True), nullable=False),
        sa.Column("iban", sa.String(34), nullable=False),
        sa.Column("data_inizio", sa.Date, nullable=False),
        sa.Column("data_fine", sa.Date, nullable=False),
        sa.Column("saldo_iniziale", sa.Numeric(15, 2), nullable=False),
        sa.Column("saldo_finale", sa.Numeric(15, 2), nullable=False),
        sa.Column("filename", sa.String(255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("created_by", UUID(as_uuid=True), nullable=True),
    )
    op.create_index("ix_bank_statements_studio_id", "bank_statements", ["studio_id"])
    op.create_index("ix_bank_statements_client_entity_id", "bank_statements", ["client_entity_id"])

    # ── bank_transactions ──────────────────────────────────────────────────────
    op.create_table(
        "bank_transactions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("studio_id", UUID(as_uuid=True), nullable=False),
        sa.Column("bank_statement_id", UUID(as_uuid=True), nullable=False),
        sa.Column("data_valuta", sa.Date, nullable=False),
        sa.Column("data_contabile", sa.Date, nullable=False),
        sa.Column("descrizione", sa.String(500), nullable=False),
        sa.Column("importo", sa.Numeric(15, 2), nullable=False),
        sa.Column("tipo", sa.String(10), nullable=False),
        sa.Column(
            "stato_riconciliazione",
            sa.String(15),
            nullable=False,
            server_default="da_riconciliare",
        ),
        sa.Column("journal_entry_id", UUID(as_uuid=True), nullable=True),
        sa.Column("scheduled_payment_id", UUID(as_uuid=True), nullable=True),
        sa.Column("note", sa.String(500), nullable=True),
    )
    op.create_index("ix_bank_transactions_studio_id", "bank_transactions", ["studio_id"])
    op.create_index(
        "ix_bank_transactions_bank_statement_id", "bank_transactions", ["bank_statement_id"]
    )

    # ── conservatore_logs ──────────────────────────────────────────────────────
    op.create_table(
        "conservatore_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("studio_id", UUID(as_uuid=True), nullable=False),
        sa.Column("client_entity_id", UUID(as_uuid=True), nullable=False),
        sa.Column("tipo_documento", sa.String(50), nullable=False),
        sa.Column("fiscal_year_id", UUID(as_uuid=True), nullable=True),
        sa.Column("periodo", sa.String(20), nullable=True),
        sa.Column("stato", sa.String(15), nullable=False, server_default="da_inviare"),
        sa.Column("data_invio", sa.Date, nullable=True),
        sa.Column("riferimento_esterno", sa.String(100), nullable=True),
        sa.Column("note", sa.String(500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("created_by", UUID(as_uuid=True), nullable=True),
    )
    op.create_index("ix_conservatore_logs_studio_id", "conservatore_logs", ["studio_id"])
    op.create_index(
        "ix_conservatore_logs_client_entity_id", "conservatore_logs", ["client_entity_id"]
    )


def downgrade() -> None:
    op.drop_table("conservatore_logs")
    op.drop_table("bank_transactions")
    op.drop_table("bank_statements")
    op.drop_table("studio_tasks")
