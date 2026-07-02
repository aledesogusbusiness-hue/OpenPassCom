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
