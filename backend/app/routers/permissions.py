"""
Router — Permessi granulari per cliente (Phase 8, solo admin).
"""
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role
from app.models.auth import User
from app.schemas.auth import ClientPermissionCreate, ClientPermissionOut
from app.services import parties_service, user_service

router = APIRouter(prefix="/api/v1/clients/{client_id}/permissions", tags=["Permessi"])


async def _get_client_or_404(db: AsyncSession, client_id: uuid.UUID):
    client = await parties_service.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente non trovato")
    return client


@router.get("", response_model=List[ClientPermissionOut])
async def list_permissions(
    client_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> List[ClientPermissionOut]:
    await _get_client_or_404(db, client_id)
    perms = await user_service.list_client_permissions(db, client_id)
    return [ClientPermissionOut.model_validate(p) for p in perms]


@router.post("", response_model=ClientPermissionOut, status_code=status.HTTP_201_CREATED)
async def grant_permission(
    client_id: uuid.UUID,
    body: ClientPermissionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> ClientPermissionOut:
    await _get_client_or_404(db, client_id)
    target_user = await user_service.get_user(db, body.user_id)
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utente non trovato")

    perm = await user_service.grant_permission(
        db, client_id, body.user_id, body.permesso, created_by=current_user.id
    )
    return ClientPermissionOut.model_validate(perm)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_permission(
    client_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> None:
    await _get_client_or_404(db, client_id)
    revoked = await user_service.revoke_permission(db, client_id, user_id)
    if not revoked:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permesso non trovato")
