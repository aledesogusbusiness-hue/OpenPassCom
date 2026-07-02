"""Phase 2 — Prima nota, IVA, Scadenzario

Revision ID: 0002
Revises: 0001
Create Date: 2025-01-01 01:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── sequence_counters ──────────────────────────────────────────────────────
    op.create_table(
        "sequence_counters",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("studio_id", UUID(as_uuid=True), nullable=False),
        sa.Column("client_entity_id", UUID(as_uuid=True), nullable=False),
        sa.Column("fiscal_year_id", UUID(as_uuid=True), nullable=False),
        sa.Column("counter_name", sa.String(50), nullable=False, server_default="journal"),
        sa.Column("last_value", sa.Integer, nullable=False, server_default="0"),
        sa.UniqueConstraint(
            "studio_id", "client_entity_id", "fiscal_year_id", "counter_name",
            name="uq_sequence_counter",
        ),
    )
    op.create_index("ix_sequence_counters_studio_id", "sequence_counters", ["studio_id"])
    op.create_index("ix_sequence_counters_client_entity_id", "sequence_counters", ["client_entity_id"])
    op.create_index("ix_sequence_counters_fiscal_year_id", "sequence_counters", ["fiscal_year_id"])

    # ── journal_entries ────────────────────────────────────────────────────────
    op.create_table(
        "journal_entries",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("studio_id", UUID(as_uuid=True), nullable=False),
        sa.Column("client_entity_id", UUID(as_uuid=True), nullable=False),
        sa.Column("fiscal_year_id", UUID(as_uuid=True), nullable=False),
        sa.Column("numero_registrazione", sa.Integer, nullable=False),
        sa.Column("data_registrazione", sa.Date, nullable=False),
        sa.Column("descrizione", sa.String(500), nullable=False),
        sa.Column("causale", sa.String(5), nullable=False),
        sa.Column("stato", sa.String(10), nullable=False, server_default="draft"),
        sa.Column("reversed_by", UUID(as_uuid=True), nullable=True),
        sa.Column("created_by", UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint(
            "studio_id", "client_entity_id", "fiscal_year_id", "numero_registrazione",
            name="uq_journal_numero",
        ),
    )
    op.create_index("ix_journal_entries_studio_id", "journal_entries", ["studio_id"])
    op.create_index("ix_journal_entries_client_entity_id", "journal_entries", ["client_entity_id"])
    op.create_index("ix_journal_entries_fiscal_year_id", "journal_entries", ["fiscal_year_id"])

    # ── journal_lines ──────────────────────────────────────────────────────────
    op.create_table(
        "journal_lines",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("studio_id", UUID(as_uuid=True), nullable=False),
        sa.Column("journal_entry_id", UUID(as_uuid=True), nullable=False),
        sa.Column("account_id", UUID(as_uuid=True), nullable=False),
        sa.Column("dare", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("avere", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("descrizione", sa.String(255), nullable=True),
        sa.CheckConstraint(
            "dare >= 0 AND avere >= 0 AND (dare + avere > 0) AND (dare = 0 OR avere = 0)",
            name="ck_journal_line_dare_avere",
        ),
        sa.ForeignKeyConstraint(["journal_entry_id"], ["journal_entries.id"], name="fk_journal_lines_entry"),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], name="fk_journal_lines_account"),
    )
    op.create_index("ix_journal_lines_studio_id", "journal_lines", ["studio_id"])
    op.create_index("ix_journal_lines_journal_entry_id", "journal_lines", ["journal_entry_id"])
    op.create_index("ix_journal_lines_account_id", "journal_lines", ["account_id"])

    # ── vat_registers ─────────────────────────────────────────────────────────
    op.create_table(
        "vat_registers",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("studio_id", UUID(as_uuid=True), nullable=False),
        sa.Column("client_entity_id", UUID(as_uuid=True), nullable=False),
        sa.Column("fiscal_year_id", UUID(as_uuid=True), nullable=False),
        sa.Column("tipo", sa.String(20), nullable=False),
        sa.UniqueConstraint(
            "studio_id", "client_entity_id", "fiscal_year_id", "tipo",
            name="uq_vat_register",
        ),
    )
    op.create_index("ix_vat_registers_studio_id", "vat_registers", ["studio_id"])
    op.create_index("ix_vat_registers_client_entity_id", "vat_registers", ["client_entity_id"])
    op.create_index("ix_vat_registers_fiscal_year_id", "vat_registers", ["fiscal_year_id"])

    # ── vat_entries ───────────────────────────────────────────────────────────
    op.create_table(
        "vat_entries",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("studio_id", UUID(as_uuid=True), nullable=False),
        sa.Column("vat_register_id", UUID(as_uuid=True), nullable=False),
        sa.Column("journal_entry_id", UUID(as_uuid=True), nullable=False),
        sa.Column("data_documento", sa.Date, nullable=False),
        sa.Column("numero_documento", sa.String(50), nullable=True),
        sa.Column("controparte", sa.String(255), nullable=True),
        sa.Column("imponibile", sa.Numeric(15, 2), nullable=False),
        sa.Column("aliquota", sa.Integer, nullable=False),
        sa.Column("imposta", sa.Numeric(15, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["vat_register_id"], ["vat_registers.id"], name="fk_vat_entries_register"),
        sa.ForeignKeyConstraint(["journal_entry_id"], ["journal_entries.id"], name="fk_vat_entries_entry"),
    )
    op.create_index("ix_vat_entries_studio_id", "vat_entries", ["studio_id"])
    op.create_index("ix_vat_entries_vat_register_id", "vat_entries", ["vat_register_id"])
    op.create_index("ix_vat_entries_journal_entry_id", "vat_entries", ["journal_entry_id"])

    # ── payment_schedules ─────────────────────────────────────────────────────
    op.create_table(
        "payment_schedules",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("studio_id", UUID(as_uuid=True), nullable=False),
        sa.Column("client_entity_id", UUID(as_uuid=True), nullable=False),
        sa.Column("journal_entry_id", UUID(as_uuid=True), nullable=True),
        sa.Column("descrizione", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_payment_schedules_studio_id", "payment_schedules", ["studio_id"])
    op.create_index("ix_payment_schedules_client_entity_id", "payment_schedules", ["client_entity_id"])

    # ── scheduled_payments ────────────────────────────────────────────────────
    op.create_table(
        "scheduled_payments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("studio_id", UUID(as_uuid=True), nullable=False),
        sa.Column("payment_schedule_id", UUID(as_uuid=True), nullable=False),
        sa.Column("data_scadenza", sa.Date, nullable=False),
        sa.Column("importo", sa.Numeric(15, 2), nullable=False),
        sa.Column("tipo", sa.String(10), nullable=False),
        sa.Column("stato", sa.String(10), nullable=False, server_default="aperto"),
        sa.Column("data_pagamento", sa.Date, nullable=True),
        sa.Column("note", sa.String(500), nullable=True),
        sa.ForeignKeyConstraint(["payment_schedule_id"], ["payment_schedules.id"], name="fk_scheduled_payments_schedule"),
    )
    op.create_index("ix_scheduled_payments_studio_id", "scheduled_payments", ["studio_id"])
    op.create_index("ix_scheduled_payments_payment_schedule_id", "scheduled_payments", ["payment_schedule_id"])


def downgrade() -> None:
    op.drop_table("scheduled_payments")
    op.drop_table("payment_schedules")
    op.drop_table("vat_entries")
    op.drop_table("vat_registers")
    op.drop_table("journal_lines")
    op.drop_table("journal_entries")
    op.drop_table("sequence_counters")
