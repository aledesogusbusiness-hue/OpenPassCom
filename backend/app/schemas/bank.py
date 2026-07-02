"""
Schemi Pydantic v2 — Phase 6: Riconciliazione bancaria e Conservatore digitale.
Campi monetari usano Decimal (mai float).
"""
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List

from pydantic import BaseModel, Field


# ── BankStatement ──────────────────────────────────────────────────────────────

class BankStatementCreate(BaseModel):
    iban: str = Field(max_length=34)
    data_inizio: date
    data_fine: date
    saldo_iniziale: Decimal
    saldo_finale: Decimal
    filename: Optional[str] = Field(default=None, max_length=255)


class BankStatementOut(BaseModel):
    id: uuid.UUID
    studio_id: uuid.UUID
    client_entity_id: uuid.UUID
    iban: str
    data_inizio: date
    data_fine: date
    saldo_iniziale: Decimal
    saldo_finale: Decimal
    filename: Optional[str]
    created_at: datetime
    created_by: Optional[uuid.UUID]

    model_config = {"from_attributes": True}


# ── BankTransaction ────────────────────────────────────────────────────────────

class BankTransactionCreate(BaseModel):
    data_valuta: date
    data_contabile: date
    descrizione: str = Field(max_length=500)
    importo: Decimal
    tipo: str = Field(pattern=r"^(entrata|uscita)$")
    note: Optional[str] = Field(default=None, max_length=500)


class BankTransactionOut(BaseModel):
    id: uuid.UUID
    studio_id: uuid.UUID
    bank_statement_id: uuid.UUID
    data_valuta: date
    data_contabile: date
    descrizione: str
    importo: Decimal
    tipo: str
    stato_riconciliazione: str
    journal_entry_id: Optional[uuid.UUID]
    scheduled_payment_id: Optional[uuid.UUID]
    note: Optional[str]

    model_config = {"from_attributes": True}


class ReconcileIn(BaseModel):
    journal_entry_id: Optional[uuid.UUID] = None
    scheduled_payment_id: Optional[uuid.UUID] = None
    note: Optional[str] = Field(default=None, max_length=500)


class ReconciliationSummaryOut(BaseModel):
    totale: int
    riconciliate: int
    da_riconciliare: int
    irrilevanti: int
    saldo_riconciliato: Decimal


# ── ConservatoreLog ────────────────────────────────────────────────────────────

class ConservatoreLogCreate(BaseModel):
    tipo_documento: str = Field(max_length=50)
    fiscal_year_id: Optional[uuid.UUID] = None
    periodo: Optional[str] = Field(default=None, max_length=20)
    note: Optional[str] = Field(default=None, max_length=500)


class ConservatoreLogOut(BaseModel):
    id: uuid.UUID
    studio_id: uuid.UUID
    client_entity_id: uuid.UUID
    tipo_documento: str
    fiscal_year_id: Optional[uuid.UUID]
    periodo: Optional[str]
    stato: str
    data_invio: Optional[date]
    riferimento_esterno: Optional[str]
    note: Optional[str]
    created_at: datetime
    created_by: Optional[uuid.UUID]

    model_config = {"from_attributes": True}


class MarkInviatoIn(BaseModel):
    data_invio: date
    riferimento_esterno: Optional[str] = Field(default=None, max_length=100)


class MarkErroreIn(BaseModel):
    note: str = Field(max_length=500)
