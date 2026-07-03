"""
Router — Gestione utenti dello studio (Phase 8, solo admin).
"""
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role
from app.models.auth import User
from app.schemas.auth import UserCreate, UserOut, UserUpdate
from app.services import user_service

router = APIRouter(prefix="/api/v1/users", tags=["Utenti"])


async def _get_user_or_404(db: AsyncSession, user_id: uuid.UUID) -> User:
    user = await user_service.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utente non trovato")
    return user


@router.get("", response_model=List[UserOut])
async def list_users(
    include_inactive: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> List[UserOut]:
    users = await user_service.list_users(db, include_inactive=include_inactive)
    return [UserOut.model_validate(u) for u in users]


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> UserOut:
    user = await user_service.create_user(db, body)
    return UserOut.model_validate(user)


@router.get("/{user_id}", response_model=UserOut)
async def get_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> UserOut:
    user = await _get_user_or_404(db, user_id)
    return UserOut.model_validate(user)


@router.patch("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: uuid.UUID,
    body: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> UserOut:
    if user_id == current_user.id and body.role is not None and body.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Non puoi rimuovere il ruolo admin dal tuo stesso account",
        )
    user = await _get_user_or_404(db, user_id)
    user = await user_service.update_user(db, user, body)
    return UserOut.model_validate(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> None:
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Non puoi disattivare il tuo stesso account",
        )
    user = await _get_user_or_404(db, user_id)
    await user_service.deactivate_user(db, user)
