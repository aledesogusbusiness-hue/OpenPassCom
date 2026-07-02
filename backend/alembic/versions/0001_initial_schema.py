"""Schema iniziale — tabelle, tipi di conto, seed studio e admin

Revision ID: 0001
Revises:
Create Date: 2025-01-01 00:00:00.000000

"""
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

STUDIO_ID = "00000000-0000-0000-0000-000000000001"


def upgrade() -> None:
    # ── users ──────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("studio_id", UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("role", sa.String(20), nullable=False, server_default="accountant"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_studio_id", "users", ["studio_id"])
    op.create_index("ix_users_email", "users", ["email"])

    # ── audit_logs ─────────────────────────────────────────────────────────────
    op.create_table(
        "audit_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("studio_id", UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=True),
        sa.Column("entity_id", sa.String(100), nullable=True),
        sa.Column("payload", JSONB, nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_audit_logs_studio_id", "audit_logs", ["studio_id"])
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])

    # ── client_entities ────────────────────────────────────────────────────────
    op.create_table(
        "client_entities",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("studio_id", UUID(as_uuid=True), nullable=False),
        sa.Column("ragione_sociale", sa.String(255), nullable=False),
        sa.Column("codice_fiscale", sa.String(16), nullable=True),
        sa.Column("partita_iva", sa.String(11), nullable=True, unique=True),
        sa.Column("fiscal_regime", sa.String(20), nullable=False, server_default="ordinario"),
        sa.Column("periodicita_iva", sa.String(20), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("note", sa.String(2000), nullable=True),
        sa.Column("created_by", UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_client_entities_studio_id", "client_entities", ["studio_id"])
    op.create_index("ix_client_entities_codice_fiscale", "client_entities", ["codice_fiscale"])
    op.create_index("ix_client_entities_partita_iva", "client_entities", ["partita_iva"])

    # ── fiscal_years ───────────────────────────────────────────────────────────
    op.create_table(
        "fiscal_years",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("studio_id", UUID(as_uuid=True), nullable=False),
        sa.Column("client_entity_id", UUID(as_uuid=True), nullable=False),
        sa.Column("anno", sa.Integer, nullable=False),
        sa.Column("data_inizio", sa.Date, nullable=False),
        sa.Column("data_fine", sa.Date, nullable=False),
        sa.Column("stato", sa.String(10), nullable=False, server_default="aperto"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", UUID(as_uuid=True), nullable=True),
        sa.UniqueConstraint("client_entity_id", "anno", name="uq_fiscal_year_client_anno"),
        sa.CheckConstraint("data_fine > data_inizio", name="ck_fiscal_year_date_order"),
    )
    op.create_index("ix_fiscal_years_studio_id", "fiscal_years", ["studio_id"])
    op.create_index("ix_fiscal_years_client_entity_id", "fiscal_years", ["client_entity_id"])

    # ── account_types ──────────────────────────────────────────────────────────
    op.create_table(
        "account_types",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tipo_codice", sa.String(10), unique=True, nullable=False),
        sa.Column("nome", sa.String(100), nullable=False),
        sa.Column("posizione_bilancio", sa.String(50), nullable=False),
    )

    # ── account_plans ──────────────────────────────────────────────────────────
    op.create_table(
        "account_plans",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("studio_id", UUID(as_uuid=True), nullable=False),
        sa.Column("client_entity_id", UUID(as_uuid=True), nullable=False),
        sa.Column("nome", sa.String(255), nullable=False),
        sa.Column("is_default", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_account_plans_studio_id", "account_plans", ["studio_id"])
    op.create_index("ix_account_plans_client_entity_id", "account_plans", ["client_entity_id"])

    # ── accounts ───────────────────────────────────────────────────────────────
    op.create_table(
        "accounts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("studio_id", UUID(as_uuid=True), nullable=False),
        sa.Column("account_plan_id", UUID(as_uuid=True), nullable=False),
        sa.Column("account_type_id", UUID(as_uuid=True), nullable=False),
        sa.Column("codice", sa.String(20), nullable=False),
        sa.Column("nome", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("livello", sa.Integer, nullable=False, server_default="1"),
        sa.Column("parent_id", UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("account_plan_id", "codice", name="uq_account_plan_codice"),
    )
    op.create_index("ix_accounts_studio_id", "accounts", ["studio_id"])
    op.create_index("ix_accounts_account_plan_id", "accounts", ["account_plan_id"])
    op.create_index("ix_accounts_account_type_id", "accounts", ["account_type_id"])
    op.create_index("ix_accounts_parent_id", "accounts", ["parent_id"])

    # ── Seed: tipi di conto ───────────────────────────────────────────────────
    account_types_table = sa.table(
        "account_types",
        sa.column("id", UUID(as_uuid=True)),
        sa.column("tipo_codice", sa.String),
        sa.column("nome", sa.String),
        sa.column("posizione_bilancio", sa.String),
    )

    AT_SP_A = uuid.UUID("10000000-0000-0000-0000-000000000001")
    AT_SP_P = uuid.UUID("10000000-0000-0000-0000-000000000002")
    AT_CE_C = uuid.UUID("10000000-0000-0000-0000-000000000003")
    AT_CE_R = uuid.UUID("10000000-0000-0000-0000-000000000004")

    op.bulk_insert(account_types_table, [
        {"id": AT_SP_A, "tipo_codice": "SP-A", "nome": "Stato Patrimoniale Attivo", "posizione_bilancio": "Attivo"},
        {"id": AT_SP_P, "tipo_codice": "SP-P", "nome": "Stato Patrimoniale Passivo", "posizione_bilancio": "Passivo"},
        {"id": AT_CE_C, "tipo_codice": "CE-C", "nome": "Conto Economico Costi", "posizione_bilancio": "Costi"},
        {"id": AT_CE_R, "tipo_codice": "CE-R", "nome": "Conto Economico Ricavi", "posizione_bilancio": "Ricavi"},
    ])


def downgrade() -> None:
    op.drop_table("accounts")
    op.drop_table("account_plans")
    op.drop_table("account_types")
    op.drop_table("fiscal_years")
    op.drop_table("client_entities")
    op.drop_table("audit_logs")
    op.drop_table("users")
