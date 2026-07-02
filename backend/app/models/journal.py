"""
Modelli Phase 2 — Prima nota, IVA, Scadenzario.

REGOLA: usa sempre `from sqlalchemy import Uuid` (NON dialects.postgresql.UUID)
         per compatibilità SQLite nei test.
"""
import uuid
from datetime import datetime, date
from decimal import Decimal

from sqlalchemy import String, Integer, DateTime, Date, Numeric, UniqueConstraint, CheckConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class JournalEntry(Base):
    """Prima nota / Registrazione contabile."""

    __tablename__ = "journal_entries"

    __table_args__ = (
        UniqueConstraint(
            "studio_id", "client_entity_id", "fiscal_year_id", "numero_registrazione",
            name="uq_journal_numero",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    studio_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    client_entity_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    fiscal_year_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    numero_registrazione: Mapped[int] = mapped_column(Integer, nullable=False)
    data_registrazione: Mapped[date] = mapped_column(Date, nullable=False)
    descrizione: Mapped[str] = mapped_column(String(500), nullable=False)
    causale: Mapped[str] = mapped_column(String(5), nullable=False)  # FV|FA|IN|PG|PN
    stato: Mapped[str] = mapped_column(String(10), nullable=False, default="draft")  # draft|posted|reversed
    reversed_by: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class JournalLine(Base):
    """Riga di registrazione contabile."""

    __tablename__ = "journal_lines"

    __table_args__ = (
        CheckConstraint(
            "dare >= 0 AND avere >= 0 AND (dare + avere > 0) AND (dare = 0 OR avere = 0)",
            name="ck_journal_line_dare_avere",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    studio_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    journal_entry_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    account_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    dare: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0"))
    avere: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0"))
    descrizione: Mapped[str | None] = mapped_column(String(255), nullable=True)


class SequenceCounter(Base):
    """Contatore numerazione progressiva (no SQL SEQUENCE — usa SELECT FOR UPDATE)."""

    __tablename__ = "sequence_counters"

    __table_args__ = (
        UniqueConstraint(
            "studio_id", "client_entity_id", "fiscal_year_id", "counter_name",
            name="uq_sequence_counter",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    studio_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    client_entity_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    fiscal_year_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    counter_name: Mapped[str] = mapped_column(String(50), nullable=False, default="journal")
    last_value: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class VatRegister(Base):
    """Registro IVA (uno per cliente, esercizio, tipo)."""

    __tablename__ = "vat_registers"

    __table_args__ = (
        UniqueConstraint(
            "studio_id", "client_entity_id", "fiscal_year_id", "tipo",
            name="uq_vat_register",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    studio_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    client_entity_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    fiscal_year_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)  # vendite|acquisti


class VatEntry(Base):
    """Riga del registro IVA."""

    __tablename__ = "vat_entries"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    studio_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    vat_register_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    journal_entry_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    data_documento: Mapped[date] = mapped_column(Date, nullable=False)
    numero_documento: Mapped[str | None] = mapped_column(String(50), nullable=True)
    controparte: Mapped[str | None] = mapped_column(String(255), nullable=True)
    imponibile: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    aliquota: Mapped[int] = mapped_column(Integer, nullable=False)  # 0, 4, 5, 10, 22
    imposta: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class PaymentSchedule(Base):
    """Intestazione scadenzario."""

    __tablename__ = "payment_schedules"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    studio_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    client_entity_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    journal_entry_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    descrizione: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ScheduledPayment(Base):
    """Scadenza singola (rata del scadenzario)."""

    __tablename__ = "scheduled_payments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    studio_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    payment_schedule_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    data_scadenza: Mapped[date] = mapped_column(Date, nullable=False)
    importo: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    tipo: Mapped[str] = mapped_column(String(10), nullable=False)  # incasso|pagamento
    stato: Mapped[str] = mapped_column(String(10), nullable=False, default="aperto")  # aperto|pagato|annullato
    data_pagamento: Mapped[date | None] = mapped_column(Date, nullable=True)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)
