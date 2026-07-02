import uuid
from datetime import datetime, date
from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator


class ClientEntityCreate(BaseModel):
    ragione_sociale: str = Field(min_length=1, max_length=255)
    codice_fiscale: Optional[str] = Field(default=None, max_length=16)
    partita_iva: Optional[str] = Field(default=None, max_length=11)
    fiscal_regime: Literal["ordinario", "semplificato", "forfettario"] = "ordinario"
    periodicita_iva: Optional[Literal["mensile", "trimestrale"]] = None
    note: Optional[str] = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def check_forfettario_no_iva(self) -> "ClientEntityCreate":
        if self.fiscal_regime == "forfettario" and self.periodicita_iva is not None:
            raise ValueError("Il regime forfettario non prevede periodicità IVA")
        if self.fiscal_regime in ("ordinario", "semplificato") and self.periodicita_iva is None:
            raise ValueError("I regimi ordinario e semplificato richiedono la periodicità IVA")
        return self


class ClientEntityUpdate(BaseModel):
    ragione_sociale: Optional[str] = Field(default=None, min_length=1, max_length=255)
    codice_fiscale: Optional[str] = Field(default=None, max_length=16)
    partita_iva: Optional[str] = Field(default=None, max_length=11)
    fiscal_regime: Optional[Literal["ordinario", "semplificato", "forfettario"]] = None
    periodicita_iva: Optional[Literal["mensile", "trimestrale"]] = None
    note: Optional[str] = Field(default=None, max_length=2000)


class ClientEntityOut(BaseModel):
    id: uuid.UUID
    studio_id: uuid.UUID
    ragione_sociale: str
    codice_fiscale: Optional[str]
    partita_iva: Optional[str]
    fiscal_regime: str
    periodicita_iva: Optional[str]
    is_active: bool
    note: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FiscalYearCreate(BaseModel):
    anno: int = Field(ge=2000, le=2100)
    data_inizio: date
    data_fine: date

    @model_validator(mode="after")
    def check_dates(self) -> "FiscalYearCreate":
        if self.data_fine <= self.data_inizio:
            raise ValueError("La data di fine deve essere successiva alla data di inizio")
        return self


class FiscalYearOut(BaseModel):
    id: uuid.UUID
    studio_id: uuid.UUID
    client_entity_id: uuid.UUID
    anno: int
    data_inizio: date
    data_fine: date
    stato: str
    created_at: datetime

    model_config = {"from_attributes": True}
