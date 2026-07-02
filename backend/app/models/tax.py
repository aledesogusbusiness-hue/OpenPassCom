"""
Modelli Phase 3 — Liquidazione IVA, Ritenute d'acconto, FatturaPA Import.

REGOLA: usa sempre `from sqlalchemy import Uuid` (NON dialects.postgresql.UUID)
         per compatibilità SQLite nei test.
"""
import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from sqlalchemy import String, Integer, DateTime, Date, Numeric, Text, JSON, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class VatSettlement(Base):
    """Liquidazione IVA periodica (mensile o trimestrale)."""

    __tablename__ = "vat_settlements"

    __table_args__ = (
        UniqueConstraint(
            "studio_id", "client_entity_id", "fiscal_year_id", "periodo",
            name="uq_vat_settlement_periodo",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    studio_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    client_entity_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    fiscal_year_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    periodo: Mapped[str] = mapped_column(String(10), nullable=False)       # '2024-03' | '2024-Q1'
    tipo_periodo: Mapped[str] = mapped_column(String(10), nullable=False)  # 'mensile' | 'trimestrale'
    iva_vendite: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0"))
    iva_acquisti: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0"))
    credito_precedente: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0"))
    debito_versare: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0"))
    credito_periodo: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0"))
    stato: Mapped[str] = mapped_column(String(10), nullable=False, default="bozza")
    data_versamento: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    f24_riferimento: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), nullable=True)


class WithholdingTax(Base):
    """Ritenuta d'acconto."""

    __tablename__ = "withholding_taxes"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    studio_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    client_entity_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    fiscal_year_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    journal_entry_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), nullable=True)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)  # professionale | occasionale | autonomo
    codice_tributo: Mapped[str] = mapped_column(String(10), nullable=False, default="1040")
    imponibile: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    aliquota_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    importo_ritenuta: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    mese_competenza: Mapped[int] = mapped_column(Integer, nullable=False)
    anno_competenza: Mapped[int] = mapped_column(Integer, nullable=False)
    stato: Mapped[str] = mapped_column(String(10), nullable=False, default="da_versare")
    data_versamento: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    f24_riferimento: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class FatturaPAImport(Base):
    """Traccia import FatturaPA XML."""

    __tablename__ = "fattura_pa_imports"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    studio_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    client_entity_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    fiscal_year_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    xml_content: Mapped[str] = mapped_column(Text, nullable=False)
    parsed_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    stato: Mapped[str] = mapped_column(String(20), nullable=False, default="importata")
    journal_entry_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), nullable=True)
    errore_msg: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
