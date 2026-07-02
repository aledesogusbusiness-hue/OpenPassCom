"""
Modelli Phase 4 — Cespiti, Ammortamenti, Chiusura esercizio.

REGOLA: usa sempre `from sqlalchemy import Uuid` (NON dialects.postgresql.UUID)
         per compatibilità SQLite nei test.
"""
import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    String, Boolean, Integer, DateTime, Date,
    Numeric, UniqueConstraint, Uuid, func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class FixedAsset(Base):
    """Cespite (bene strumentale)."""

    __tablename__ = "fixed_assets"

    __table_args__ = (
        UniqueConstraint(
            "studio_id", "client_entity_id", "codice",
            name="uq_fixed_asset_codice",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    studio_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), nullable=False, index=True
    )
    client_entity_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), nullable=False, index=True
    )
    fiscal_year_acquisto: Mapped[int] = mapped_column(Integer, nullable=False)
    codice: Mapped[str] = mapped_column(String(20), nullable=False)
    descrizione: Mapped[str] = mapped_column(String(255), nullable=False)
    categoria: Mapped[str] = mapped_column(String(50), nullable=False)
    costo_storico: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    data_acquisto: Mapped[date] = mapped_column(Date, nullable=False)
    account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), nullable=True
    )
    aliquota_ammortamento: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False
    )
    metodo: Mapped[str] = mapped_column(
        String(20), nullable=False, default="quote_costanti"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    note: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), nullable=True
    )


class DepreciationEntry(Base):
    """Quota annuale di ammortamento (piano di ammortamento)."""

    __tablename__ = "depreciation_entries"

    __table_args__ = (
        UniqueConstraint(
            "fixed_asset_id", "anno",
            name="uq_depreciation_asset_anno",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    studio_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), nullable=False, index=True
    )
    fixed_asset_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), nullable=False, index=True
    )
    anno: Mapped[int] = mapped_column(Integer, nullable=False)
    valore_iniziale: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    quota_ammortamento: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    fondo_ammortamento: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    valore_netto_finale: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    journal_entry_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), nullable=True
    )
    stato: Mapped[str] = mapped_column(
        String(10), nullable=False, default="calcolato"
    )


class YearClosing(Base):
    """Chiusura esercizio fiscale con dati di bilancio riepilogati."""

    __tablename__ = "year_closings"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    studio_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), nullable=False, index=True
    )
    client_entity_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), nullable=False, index=True
    )
    fiscal_year_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), nullable=False, unique=True
    )
    stato: Mapped[str] = mapped_column(
        String(20), nullable=False, default="in_corso"
    )
    data_chiusura: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    note: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    totale_attivo: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2), nullable=True
    )
    totale_passivo: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2), nullable=True
    )
    totale_ricavi: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2), nullable=True
    )
    totale_costi: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2), nullable=True
    )
    utile_perdita: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), nullable=True
    )
