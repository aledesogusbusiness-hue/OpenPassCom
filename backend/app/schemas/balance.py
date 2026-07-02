"""
Schemi Pydantic v2 — Phase 4: Cespiti, Ammortamenti, Bilancio, Chiusura esercizio.
Tutti i campi monetari usano Decimal (mai float).
"""
import uuid
from datetime import date
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


# ── Cespiti ──────────────────────────────────────────────────────────────────

class FixedAssetCreate(BaseModel):
    codice: str
    descrizione: str
    categoria: str
    costo_storico: Decimal
    data_acquisto: date
    aliquota_ammortamento: Decimal
    metodo: str = "quote_costanti"
    account_id: Optional[uuid.UUID] = None
    note: Optional[str] = None


class FixedAssetOut(BaseModel):
    id: uuid.UUID
    codice: str
    descrizione: str
    categoria: str
    costo_storico: Decimal
    data_acquisto: date
    aliquota_ammortamento: Decimal
    metodo: str
    is_active: bool
    note: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class DepreciationEntryOut(BaseModel):
    id: uuid.UUID
    anno: int
    valore_iniziale: Decimal
    quota_ammortamento: Decimal
    fondo_ammortamento: Decimal
    valore_netto_finale: Decimal
    stato: str

    model_config = ConfigDict(from_attributes=True)


class RegistroCespiteRow(BaseModel):
    asset: FixedAssetOut
    quota_anno: Optional[Decimal]
    fondo_cumulato: Optional[Decimal]
    valore_netto: Optional[Decimal]


# ── Bilancio ─────────────────────────────────────────────────────────────────

class VoceBilancio(BaseModel):
    codice: str
    nome: str
    saldo: Decimal


class SezionePatrimoniale(BaseModel):
    voci: List[VoceBilancio]
    totale: Decimal


class StatoPatrimonialeOut(BaseModel):
    attivo: SezionePatrimoniale
    passivo: SezionePatrimoniale
    totale_attivo: Decimal
    totale_passivo: Decimal
    quadrato: bool


class SezioneEconomica(BaseModel):
    voci: List[VoceBilancio]
    totale: Decimal


class ContoEconomicoOut(BaseModel):
    ricavi: SezioneEconomica
    costi: SezioneEconomica
    risultato_operativo: Decimal
    utile_perdita: Decimal


# ── Chiusura esercizio ────────────────────────────────────────────────────────

class YearClosingCreate(BaseModel):
    note: Optional[str] = None


class YearClosingOut(BaseModel):
    id: uuid.UUID
    fiscal_year_id: uuid.UUID
    stato: str
    data_chiusura: Optional[date]
    totale_attivo: Optional[Decimal]
    totale_passivo: Optional[Decimal]
    totale_ricavi: Optional[Decimal]
    totale_costi: Optional[Decimal]
    utile_perdita: Optional[Decimal]
    note: Optional[str]

    model_config = ConfigDict(from_attributes=True)
