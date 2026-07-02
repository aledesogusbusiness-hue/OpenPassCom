"""
Schemi Pydantic v2 — Phase 5: Studio Task Management e Dashboard.
Tutti i campi monetari usano Decimal (mai float).
"""
import uuid
from datetime import date, datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class StudioTaskCreate(BaseModel):
    client_entity_id: Optional[uuid.UUID] = None
    fiscal_year_id: Optional[uuid.UUID] = None
    titolo: str = Field(max_length=255)
    descrizione: Optional[str] = Field(default=None, max_length=2000)
    tipo: str = Field(pattern=r"^(scadenza_iva|versamento_ritenute|chiusura_bilancio|generico)$")
    priorita: str = Field(default="normale", pattern=r"^(bassa|normale|alta|urgente)$")
    data_scadenza: Optional[date] = None
    assegnato_a: Optional[uuid.UUID] = None
    note: Optional[str] = Field(default=None, max_length=1000)


class StudioTaskUpdate(BaseModel):
    titolo: Optional[str] = Field(default=None, max_length=255)
    descrizione: Optional[str] = Field(default=None, max_length=2000)
    priorita: Optional[str] = Field(default=None, pattern=r"^(bassa|normale|alta|urgente)$")
    data_scadenza: Optional[date] = None
    assegnato_a: Optional[uuid.UUID] = None
    note: Optional[str] = Field(default=None, max_length=1000)


class StudioTaskOut(BaseModel):
    id: uuid.UUID
    studio_id: uuid.UUID
    client_entity_id: Optional[uuid.UUID]
    fiscal_year_id: Optional[uuid.UUID]
    titolo: str
    descrizione: Optional[str]
    tipo: str
    priorita: str
    stato: str
    data_scadenza: Optional[date]
    assegnato_a: Optional[uuid.UUID]
    completato_il: Optional[date]
    note: Optional[str]
    created_at: datetime
    created_by: Optional[uuid.UUID]

    model_config = {"from_attributes": True}


class CompleteTaskIn(BaseModel):
    completato_il: date


class DashboardSummaryOut(BaseModel):
    clienti_attivi: int
    task_aperti: int
    task_urgenti: int
    scadenze_questa_settimana: int
    liquidazioni_bozza: int
    ritenute_da_versare: int
    fatture_importate: int
