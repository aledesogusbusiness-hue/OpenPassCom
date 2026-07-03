"""
Schemi Pydantic v2 — Phase 3: Liquidazione IVA, Ritenute, FatturaPA.
Tutti i campi monetari usano Decimal (mai float).
"""
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── VAT Settlement ────────────────────────────────────────────────────────────

class VatSettlementCreate(BaseModel):
    periodo: str = Field(description="Es. '2024-03' (mensile) o '2024-Q1' (trimestrale)")
    credito_precedente: Decimal = Field(default=Decimal("0"), ge=0)


class VatSettlementOut(BaseModel):
    id: uuid.UUID
    studio_id: uuid.UUID
    client_entity_id: uuid.UUID
    fiscal_year_id: uuid.UUID
    periodo: str
    tipo_periodo: str
    iva_vendite: Decimal
    iva_acquisti: Decimal
    credito_precedente: Decimal
    debito_versare: Decimal
    credito_periodo: Decimal
    stato: str
    data_versamento: Optional[date]
    f24_riferimento: Optional[str]
    created_at: datetime
    created_by: Optional[uuid.UUID]

    model_config = {"from_attributes": True}


class MarkVersataSettlementIn(BaseModel):
    data_versamento: date
    f24_riferimento: Optional[str] = None


# ── F24 ───────────────────────────────────────────────────────────────────────

class F24Riga(BaseModel):
    codice_tributo: str
    descrizione: str
    importo: Decimal


class F24ProspettoOut(BaseModel):
    periodo: str
    tipo_periodo: str
    sezione_erario: List[F24Riga]
    sezione_contributi: List[F24Riga] = []
    totale_saldo: Decimal


# ── Withholding Tax ───────────────────────────────────────────────────────────

class WithholdingTaxCreate(BaseModel):
    tipo: str = Field(pattern=r"^(professionale|occasionale|autonomo)$")
    codice_tributo: str = Field(default="1040", max_length=10)
    imponibile: Decimal = Field(gt=0)
    aliquota_pct: Decimal = Field(gt=0, le=100)
    mese_competenza: int = Field(ge=1, le=12)
    anno_competenza: int = Field(ge=2000)
    journal_entry_id: Optional[uuid.UUID] = None


class WithholdingTaxOut(BaseModel):
    id: uuid.UUID
    studio_id: uuid.UUID
    client_entity_id: uuid.UUID
    fiscal_year_id: uuid.UUID
    journal_entry_id: Optional[uuid.UUID]
    tipo: str
    codice_tributo: str
    imponibile: Decimal
    aliquota_pct: Decimal
    importo_ritenuta: Decimal
    mese_competenza: int
    anno_competenza: int
    stato: str
    data_versamento: Optional[date]
    f24_riferimento: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class WithholdingMarkVersataIn(BaseModel):
    data_versamento: date
    f24_riferimento: Optional[str] = None


class F24RitenutaRiga(BaseModel):
    codice_tributo: str
    importo: Decimal


class F24RitenutaOut(BaseModel):
    mese: int
    anno: int
    righe: List[F24RitenutaRiga]
    totale: Decimal


# ── FatturaPA Import ──────────────────────────────────────────────────────────

class FatturaPAImportIn(BaseModel):
    filename: str = Field(max_length=255)
    xml_content: str


class FatturaPAImportOut(BaseModel):
    id: uuid.UUID
    studio_id: uuid.UUID
    client_entity_id: uuid.UUID
    fiscal_year_id: uuid.UUID
    filename: str
    stato: str
    parsed_data: Optional[Dict[str, Any]]
    journal_entry_id: Optional[uuid.UUID]
    errore_msg: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class FatturaPAElaborateIn(BaseModel):
    account_id_fornitore: uuid.UUID
    account_id_iva: uuid.UUID
    account_id_debito: uuid.UUID


# ── FatturaPA Export (Phase 9 — infrastruttura invio SDI) ─────────────────────

class FatturaPAExportLineIn(BaseModel):
    descrizione: str = Field(min_length=1, max_length=1000)
    quantita: Decimal = Field(default=Decimal("1"), gt=0)
    unita_misura: Optional[str] = Field(default=None, max_length=10)
    prezzo_unitario: Decimal = Field(gt=0)
    aliquota_iva: int = Field(ge=0, le=22)


class FatturaPAExportLineOut(BaseModel):
    id: uuid.UUID
    numero_linea: int
    descrizione: str
    quantita: Decimal
    unita_misura: Optional[str]
    prezzo_unitario: Decimal
    aliquota_iva: Decimal

    model_config = {"from_attributes": True}


class FatturaPAExportCreate(BaseModel):
    journal_entry_id: Optional[uuid.UUID] = None
    tipo_documento: str = Field(default="TD01", pattern=r"^TD(0[1-9]|2[0-8])$")
    numero_fattura: str = Field(min_length=1, max_length=20)
    data_fattura: date

    cedente_indirizzo: str = Field(min_length=1, max_length=255)
    cedente_cap: str = Field(min_length=5, max_length=5)
    cedente_comune: str = Field(min_length=1, max_length=100)
    cedente_provincia: str = Field(min_length=2, max_length=2)

    destinatario_denominazione: str = Field(min_length=1, max_length=255)
    destinatario_partita_iva: Optional[str] = Field(default=None, max_length=11)
    destinatario_codice_fiscale: Optional[str] = Field(default=None, max_length=16)
    destinatario_indirizzo: str = Field(min_length=1, max_length=255)
    destinatario_cap: str = Field(min_length=5, max_length=5)
    destinatario_comune: str = Field(min_length=1, max_length=100)
    destinatario_provincia: str = Field(min_length=2, max_length=2)
    destinatario_codice_sdi: str = Field(default="0000000", max_length=7)
    destinatario_pec: Optional[str] = Field(default=None, max_length=255)

    righe: List[FatturaPAExportLineIn] = Field(min_length=1)


class FatturaPAExportOut(BaseModel):
    id: uuid.UUID
    studio_id: uuid.UUID
    client_entity_id: uuid.UUID
    fiscal_year_id: uuid.UUID
    journal_entry_id: Optional[uuid.UUID]
    tipo_documento: str
    numero_fattura: str
    data_fattura: date
    destinatario_denominazione: str
    destinatario_partita_iva: Optional[str]
    destinatario_codice_fiscale: Optional[str]
    destinatario_codice_sdi: str
    destinatario_pec: Optional[str]
    stato: str
    progressivo_invio: Optional[str]
    identificativo_sdi: Optional[str]
    data_invio: Optional[datetime]
    data_esito: Optional[datetime]
    esito_messaggio: Optional[str]
    errore_msg: Optional[str]
    created_at: datetime
    righe: List[FatturaPAExportLineOut] = []

    model_config = {"from_attributes": True}


class FatturaPAExportMarkInviataIn(BaseModel):
    """Il progressivo_invio è assegnato automaticamente in generate_xml();
    qui si conferma solo l'avvenuto invio (manuale o da un futuro connettore SDI)."""
    identificativo_sdi: Optional[str] = Field(default=None, max_length=50)


class FatturaPAExportMarkEsitoIn(BaseModel):
    esito: str = Field(pattern=r"^(accettata|scartata|consegnata)$")
    messaggio: Optional[str] = Field(default=None, max_length=1000)
