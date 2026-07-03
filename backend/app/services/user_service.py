"""
User Service — Gestione utenti dello studio e permessi granulari per cliente (Phase 8).
"""
import uuid
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.auth import ClientUserPermission, User
from app.schemas.auth import UserCreate, UserUpdate
from app.services.auth_service import hash_password

STUDIO_UUID = uuid.UUID(settings.STUDIO_ID)


# ── Utenti ───────────────────────────────────────────────────────────────────

async def list_users(db: AsyncSession, include_inactive: bool = False) -> List[User]:
    query = select(User).where(User.studio_id == STUDIO_UUID)
    if not include_inactive:
        query = query.where(User.is_active == True)  # noqa: E712
    query = query.order_by(User.full_name)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_user(db: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
    result = await db.execute(
        select(User).where(User.id == user_id, User.studio_id == STUDIO_UUID)
    )
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, data: UserCreate) -> User:
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Esiste già un utente con questa email",
        )

    user = User(
        id=uuid.uuid4(),
        studio_id=STUDIO_UUID,
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        is_active=True,
        role=data.role,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def update_user(db: AsyncSession, user: User, data: UserUpdate) -> User:
    update_data = data.model_dump(exclude_unset=True)
    if "password" in update_data:
        password = update_data.pop("password")
        if password:
            user.hashed_password = hash_password(password)
    for field, value in update_data.items():
        setattr(user, field, value)
    await db.flush()
    await db.refresh(user)
    return user


async def deactivate_user(db: AsyncSession, user: User) -> None:
    user.is_active = False
    await db.flush()


# ── Permessi per cliente ─────────────────────────────────────────────────────

async def list_client_permissions(
    db: AsyncSession, client_entity_id: uuid.UUID
) -> List[ClientUserPermission]:
    result = await db.execute(
        select(ClientUserPermission).where(
            ClientUserPermission.client_entity_id == client_entity_id,
            ClientUserPermission.studio_id == STUDIO_UUID,
        )
    )
    return list(result.scalars().all())


async def grant_permission(
    db: AsyncSession,
    client_entity_id: uuid.UUID,
    user_id: uuid.UUID,
    permesso: str,
    created_by: uuid.UUID,
) -> ClientUserPermission:
    result = await db.execute(
        select(ClientUserPermission).where(
            ClientUserPermission.client_entity_id == client_entity_id,
            ClientUserPermission.user_id == user_id,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        existing.permesso = permesso
        await db.flush()
        await db.refresh(existing)
        return existing

    perm = ClientUserPermission(
        id=uuid.uuid4(),
        studio_id=STUDIO_UUID,
        user_id=user_id,
        client_entity_id=client_entity_id,
        permesso=permesso,
        created_by=created_by,
    )
    db.add(perm)
    await db.flush()
    await db.refresh(perm)
    return perm


async def revoke_permission(
    db: AsyncSession, client_entity_id: uuid.UUID, user_id: uuid.UUID
) -> bool:
    result = await db.execute(
        select(ClientUserPermission).where(
            ClientUserPermission.client_entity_id == client_entity_id,
            ClientUserPermission.user_id == user_id,
        )
    )
    perm = result.scalar_one_or_none()
    if not perm:
        return False
    await db.delete(perm)
    await db.flush()
    return True


async def has_client_access(
    db: AsyncSession,
    user_id: uuid.UUID,
    client_entity_id: uuid.UUID,
    require_write: bool = False,
) -> bool:
    result = await db.execute(
        select(ClientUserPermission).where(
            ClientUserPermission.user_id == user_id,
            ClientUserPermission.client_entity_id == client_entity_id,
        )
    )
    perm = result.scalar_one_or_none()
    if not perm:
        return False
    if require_write:
        return perm.permesso == "scrittura"
    return True


async def list_accessible_client_ids(db: AsyncSession, user_id: uuid.UUID) -> set[uuid.UUID]:
    result = await db.execute(
        select(ClientUserPermission.client_entity_id).where(
            ClientUserPermission.user_id == user_id,
        )
    )
    return {row[0] for row in result.all()}
