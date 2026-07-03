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


class FatturaPAExport(Base):
    """
    Fattura elettronica emessa verso SDI (Phase 9 — infrastruttura lato nostro).

    Ciclo di vita: bozza -> generata -> inviata -> accettata|scartata -> consegnata
    L'invio effettivo a SDI richiede un intermediario/accreditamento esterno:
    'inviata' ed 'esito' vengono registrati manualmente (o da un futuro
    connettore reale) tramite mark_inviata()/mark_esito().
    """

    __tablename__ = "fattura_pa_exports"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    studio_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    client_entity_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    fiscal_year_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    journal_entry_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), nullable=True)

    tipo_documento: Mapped[str] = mapped_column(String(4), nullable=False, default="TD01")
    numero_fattura: Mapped[str] = mapped_column(String(20), nullable=False)
    data_fattura: Mapped[date] = mapped_column(Date, nullable=False)

    # Cedente (il nostro cliente, chi emette la fattura) — indirizzo non presente su ClientEntity
    cedente_indirizzo: Mapped[str] = mapped_column(String(255), nullable=False)
    cedente_cap: Mapped[str] = mapped_column(String(5), nullable=False)
    cedente_comune: Mapped[str] = mapped_column(String(100), nullable=False)
    cedente_provincia: Mapped[str] = mapped_column(String(2), nullable=False)

    # Cessionario (destinatario della fattura)
    destinatario_denominazione: Mapped[str] = mapped_column(String(255), nullable=False)
    destinatario_partita_iva: Mapped[Optional[str]] = mapped_column(String(11), nullable=True)
    destinatario_codice_fiscale: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    destinatario_indirizzo: Mapped[str] = mapped_column(String(255), nullable=False)
    destinatario_cap: Mapped[str] = mapped_column(String(5), nullable=False)
    destinatario_comune: Mapped[str] = mapped_column(String(100), nullable=False)
    destinatario_provincia: Mapped[str] = mapped_column(String(2), nullable=False)
    destinatario_codice_sdi: Mapped[str] = mapped_column(String(7), nullable=False, default="0000000")
    destinatario_pec: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    xml_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    stato: Mapped[str] = mapped_column(String(20), nullable=False, default="bozza")
    # bozza | generata | inviata | accettata | scartata | consegnata | errore

    progressivo_invio: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    identificativo_sdi: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    data_invio: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    data_esito: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    esito_messaggio: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    errore_msg: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), nullable=True)


class FatturaPAExportLine(Base):
    """Riga di dettaglio (bene/servizio) di una fattura elettronica emessa."""

    __tablename__ = "fattura_pa_export_lines"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    studio_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    fattura_pa_export_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    numero_linea: Mapped[int] = mapped_column(Integer, nullable=False)
    descrizione: Mapped[str] = mapped_column(String(1000), nullable=False)
    quantita: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("1"))
    unita_misura: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    prezzo_unitario: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    aliquota_iva: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
