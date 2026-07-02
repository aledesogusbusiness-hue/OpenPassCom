"""
Modelli Phase 6 — Riconciliazione bancaria e Conservatore digitale.

REGOLA: usa sempre `from sqlalchemy import Uuid` (NON dialects.postgresql.UUID)
         per compatibilità SQLite nei test.
"""
import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from sqlalchemy import String, DateTime, Date, Numeric, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class BankStatement(Base):
    """Estratto conto bancario."""

    __tablename__ = "bank_statements"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    studio_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    client_entity_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    iban: Mapped[str] = mapped_column(String(34), nullable=False)
    data_inizio: Mapped[date] = mapped_column(Date, nullable=False)
    data_fine: Mapped[date] = mapped_column(Date, nullable=False)
    saldo_iniziale: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    saldo_finale: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), nullable=True)


class BankTransaction(Base):
    """Transazione bancaria (riga estratto conto)."""

    __tablename__ = "bank_transactions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    studio_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    bank_statement_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    data_valuta: Mapped[date] = mapped_column(Date, nullable=False)
    data_contabile: Mapped[date] = mapped_column(Date, nullable=False)
    descrizione: Mapped[str] = mapped_column(String(500), nullable=False)
    importo: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    tipo: Mapped[str] = mapped_column(String(10), nullable=False)  # entrata | uscita
    stato_riconciliazione: Mapped[str] = mapped_column(
        String(15), nullable=False, default="da_riconciliare"
    )  # da_riconciliare | riconciliata | irrilevante
    journal_entry_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), nullable=True)
    scheduled_payment_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), nullable=True)
    note: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)


class ConservatoreLog(Base):
    """Log invio documenti al conservatore digitale."""

    __tablename__ = "conservatore_logs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    studio_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    client_entity_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    tipo_documento: Mapped[str] = mapped_column(String(50), nullable=False)
    # libro_giornale | registro_iva | bilancio
    fiscal_year_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), nullable=True)
    periodo: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    stato: Mapped[str] = mapped_column(String(15), nullable=False, default="da_inviare")
    # da_inviare | inviato | confermato | errore
    data_invio: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    riferimento_esterno: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    note: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), nullable=True)
