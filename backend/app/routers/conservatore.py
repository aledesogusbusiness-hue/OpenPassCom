"""
Router — Conservatore digitale (Phase 6).
"""
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, verify_client_access
from app.models.auth import User
from app.schemas.bank import (
    ConservatoreLogCreate,
    ConservatoreLogOut,
    MarkErroreIn,
    MarkInviatoIn,
)
from app.services import conservatore_service, parties_service

router = APIRouter(prefix="/api/v1", tags=["Conservatore"], dependencies=[Depends(verify_client_access)])


async def _get_client_or_404(db: AsyncSession, client_id: uuid.UUID):
    client = await parties_service.get_client(db, client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente non trovato",
        )
    return client


async def _get_log_or_404(
    db: AsyncSession,
    client_id: uuid.UUID,
    log_id: uuid.UUID,
):
    log = await conservatore_service.get_log(db, client_id, log_id)
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Log conservatore non trovato",
        )
    return log


@router.post(
    "/clients/{client_id}/conservatore-logs",
    response_model=ConservatoreLogOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_log(
    client_id: uuid.UUID,
    body: ConservatoreLogCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ConservatoreLogOut:
    await _get_client_or_404(db, client_id)
    log = await conservatore_service.create_log(
        db, client_id, body, created_by=current_user.id
    )
    return ConservatoreLogOut.model_validate(log)


@router.get(
    "/clients/{client_id}/conservatore-logs",
    response_model=List[ConservatoreLogOut],
)
async def list_logs(
    client_id: uuid.UUID,
    stato: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[ConservatoreLogOut]:
    await _get_client_or_404(db, client_id)
    logs = await conservatore_service.list_logs(db, client_id, stato=stato)
    return [ConservatoreLogOut.model_validate(lg) for lg in logs]


@router.post(
    "/clients/{client_id}/conservatore-logs/{log_id}/mark-inviato",
    response_model=ConservatoreLogOut,
)
async def mark_inviato(
    client_id: uuid.UUID,
    log_id: uuid.UUID,
    body: MarkInviatoIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ConservatoreLogOut:
    await _get_client_or_404(db, client_id)
    log = await _get_log_or_404(db, client_id, log_id)
    log = await conservatore_service.mark_inviato(
        db, log, body.data_invio, body.riferimento_esterno
    )
    return ConservatoreLogOut.model_validate(log)


@router.post(
    "/clients/{client_id}/conservatore-logs/{log_id}/mark-confermato",
    response_model=ConservatoreLogOut,
)
async def mark_confermato(
    client_id: uuid.UUID,
    log_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ConservatoreLogOut:
    await _get_client_or_404(db, client_id)
    log = await _get_log_or_404(db, client_id, log_id)
    log = await conservatore_service.mark_confermato(db, log)
    return ConservatoreLogOut.model_validate(log)


@router.post(
    "/clients/{client_id}/conservatore-logs/{log_id}/mark-errore",
    response_model=ConservatoreLogOut,
)
async def mark_errore(
    client_id: uuid.UUID,
    log_id: uuid.UUID,
    body: MarkErroreIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ConservatoreLogOut:
    await _get_client_or_404(db, client_id)
    log = await _get_log_or_404(db, client_id, log_id)
    log = await conservatore_service.mark_errore(db, log, body.note)
    return ConservatoreLogOut.model_validate(log)
