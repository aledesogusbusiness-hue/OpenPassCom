import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserOut(BaseModel):
    id: uuid.UUID
    studio_id: uuid.UUID
    email: str
    full_name: str
    is_active: bool
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=1, max_length=255)
    role: Literal["admin", "accountant", "collaborator"] = "accountant"


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    role: Optional[Literal["admin", "accountant", "collaborator"]] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(default=None, min_length=8)


class ClientPermissionCreate(BaseModel):
    user_id: uuid.UUID
    permesso: Literal["lettura", "scrittura"] = "lettura"


class ClientPermissionOut(BaseModel):
    id: uuid.UUID
    studio_id: uuid.UUID
    user_id: uuid.UUID
    client_entity_id: uuid.UUID
    permesso: str
    created_at: datetime
    created_by: Optional[uuid.UUID]

    model_config = {"from_attributes": True}
