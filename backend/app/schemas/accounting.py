import uuid
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class AccountTypeOut(BaseModel):
    id: uuid.UUID
    tipo_codice: str
    nome: str
    posizione_bilancio: str

    model_config = {"from_attributes": True}


class AccountPlanOut(BaseModel):
    id: uuid.UUID
    studio_id: uuid.UUID
    client_entity_id: uuid.UUID
    nome: str
    is_default: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AccountCreate(BaseModel):
    account_plan_id: uuid.UUID
    account_type_id: uuid.UUID
    codice: str = Field(min_length=1, max_length=20)
    nome: str = Field(min_length=1, max_length=255)
    livello: int = Field(default=1, ge=1)
    parent_id: Optional[uuid.UUID] = None


class AccountOut(BaseModel):
    id: uuid.UUID
    studio_id: uuid.UUID
    account_plan_id: uuid.UUID
    account_type_id: uuid.UUID
    codice: str
    nome: str
    is_active: bool
    livello: int
    parent_id: Optional[uuid.UUID]
    created_at: datetime
    children: List["AccountOut"] = []

    model_config = {"from_attributes": True}


AccountOut.model_rebuild()
