"""
Schemi Pydantic v2 — Phase 2: Prima nota, IVA, Scadenzario.
Tutti i campi monetari usano Decimal (mai float).
"""
import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


# ── Journal Lines ────────────────────────────────────────────────────────────

class JournalLineIn(BaseModel):
    account_id: uuid.UUID
    dare: Decimal = Field(default=Decimal("0"), ge=0)
    avere: Decimal = Field(default=Decimal("0"), ge=0)
    descrizione: Optional[str] = Field(default=None, max_length=255)


class JournalLineOut(BaseModel):
    id: uuid.UUID
    studio_id: uuid.UUID
    journal_entry_id: uuid.UUID
    account_id: uuid.UUID
    dare: Decimal
    avere: Decimal
    descrizione: Optional[str]

    model_config = {"from_attributes": True}


# ── Journal Entries ──────────────────────────────────────────────────────────

class JournalEntryCreate(BaseModel):
    data_registrazione: date
    descrizione: str = Field(min_length=1, max_length=500)
    causale: str = Field(min_length=2, max_length=5, pattern=r"^(FV|FA|IN|PG|PN)$")
    lines: List[JournalLineIn] = Field(min_length=2)


class JournalEntryOut(BaseModel):
    id: uuid.UUID
    studio_id: uuid.UUID
    client_entity_id: uuid.UUID
    fiscal_year_id: uuid.UUID
    numero_registrazione: int
    data_registrazione: date
    descrizione: str
    causale: str
    stato: str
    reversed_by: Optional[uuid.UUID]
    created_by: Optional[uuid.UUID]
    created_at: datetime

    model_config = {"from_attributes": True}


class JournalEntryDetail(JournalEntryOut):
    lines: List[JournalLineOut] = []


# ── VAT ─────────────────────────────────────────────────────────────────────

class VatEntryCreate(BaseModel):
    tipo: str = Field(pattern=r"^(vendite|acquisti)$")
    journal_entry_id: uuid.UUID
    data_documento: date
    numero_documento: Optional[str] = Field(default=None, max_length=50)
    controparte: Optional[str] = Field(default=None, max_length=255)
    imponibile: Decimal
    aliquota: int = Field(ge=0, le=22)
    imposta: Decimal


class VatEntryOut(BaseModel):
    id: uuid.UUID
    studio_id: uuid.UUID
    vat_register_id: uuid.UUID
    journal_entry_id: uuid.UUID
    data_documento: date
    numero_documento: Optional[str]
    controparte: Optional[str]
    imponibile: Decimal
    aliquota: int
    imposta: Decimal
    created_at: datetime

    model_config = {"from_attributes": True}


class VatLiquidazioneOut(BaseModel):
    periodo: str
    iva_vendite: Decimal
    iva_acquisti: Decimal
    debito_credito: Decimal


# ── Payments / Scadenzario ───────────────────────────────────────────────────

class PaymentScheduleCreate(BaseModel):
    descrizione: Optional[str] = Field(default=None, max_length=255)
    journal_entry_id: Optional[uuid.UUID] = None


class PaymentScheduleOut(BaseModel):
    id: uuid.UUID
    studio_id: uuid.UUID
    client_entity_id: uuid.UUID
    journal_entry_id: Optional[uuid.UUID]
    descrizione: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class ScheduledPaymentCreate(BaseModel):
    data_scadenza: date
    importo: Decimal = Field(gt=0)
    tipo: str = Field(pattern=r"^(incasso|pagamento)$")
    note: Optional[str] = Field(default=None, max_length=500)


class ScheduledPaymentOut(BaseModel):
    id: uuid.UUID
    studio_id: uuid.UUID
    payment_schedule_id: uuid.UUID
    data_scadenza: date
    importo: Decimal
    tipo: str
    stato: str
    data_pagamento: Optional[date]
    note: Optional[str]

    model_config = {"from_attributes": True}


class MarkPaidIn(BaseModel):
    data_pagamento: date


# ── Mastrino / Bilancio ──────────────────────────────────────────────────────

class MastrinMovimento(BaseModel):
    journal_entry_id: uuid.UUID
    data_registrazione: date
    numero_registrazione: int
    descrizione: str
    dare: Decimal
    avere: Decimal
    saldo_progressivo: Decimal


class MastrinoOut(BaseModel):
    account_id: uuid.UUID
    movimenti: List[MastrinMovimento]
    tot_dare: Decimal
    tot_avere: Decimal
    saldo: Decimal


class BilancioVoce(BaseModel):
    account_id: uuid.UUID
    codice: str
    nome: str
    tot_dare: Decimal
    tot_avere: Decimal
    saldo: Decimal
