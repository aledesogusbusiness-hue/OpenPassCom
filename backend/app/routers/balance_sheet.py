"""
Router — Stato Patrimoniale, Conto Economico, Chiusura esercizio.

NOTA: Questo router deve essere registrato PRIMA del router parties in main.py
      perché override il medesimo percorso POST .../close per creare il YearClosing.
"""
import uuid
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.auth import User
from app.schemas.balance import (
    ContoEconomicoOut,
    StatoPatrimonialeOut,
    YearClosingCreate,
    YearClosingOut,
)
from app.services import balance_sheet_service, parties_service

router = APIRouter(prefix="/api/v1", tags=["Bilancio"])


async def _get_client_or_404(db: AsyncSession, client_id: uuid.UUID):
    client = await parties_service.get_client(db, client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente non trovato",
        )
    return client


async def _get_fiscal_year_or_404(
    db: AsyncSession, client_id: uuid.UUID, year_id: uuid.UUID
):
    fy = await parties_service.get_fiscal_year(db, client_id, year_id)
    if not fy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Esercizio fiscale non trovato",
        )
    return fy


# ── Stato Patrimoniale ────────────────────────────────────────────────────────

@router.get(
    "/clients/{client_id}/fiscal-years/{year_id}/stato-patrimoniale",
    response_model=StatoPatrimonialeOut,
)
async def get_stato_patrimoniale(
    client_id: uuid.UUID,
    year_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StatoPatrimonialeOut:
    await _get_client_or_404(db, client_id)
    await _get_fiscal_year_or_404(db, client_id, year_id)

    data = await balance_sheet_service.get_stato_patrimoniale(db, client_id, year_id)
    return StatoPatrimonialeOut(**data)


# ── Conto Economico ───────────────────────────────────────────────────────────

@router.get(
    "/clients/{client_id}/fiscal-years/{year_id}/conto-economico",
    response_model=ContoEconomicoOut,
)
async def get_conto_economico(
    client_id: uuid.UUID,
    year_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ContoEconomicoOut:
    await _get_client_or_404(db, client_id)
    await _get_fiscal_year_or_404(db, client_id, year_id)

    data = await balance_sheet_service.get_conto_economico(db, client_id, year_id)
    return ContoEconomicoOut(**data)


# ── Chiusura esercizio ────────────────────────────────────────────────────────

@router.post(
    "/clients/{client_id}/fiscal-years/{year_id}/close",
    response_model=YearClosingOut,
)
async def close_fiscal_year(
    client_id: uuid.UUID,
    year_id: uuid.UUID,
    body: Optional[YearClosingCreate] = Body(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> YearClosingOut:
    await _get_client_or_404(db, client_id)

    note = body.note if body else None
    closing = await balance_sheet_service.close_fiscal_year(
        db,
        client_entity_id=client_id,
        fiscal_year_id=year_id,
        created_by=current_user.id,
        note=note,
    )
    return YearClosingOut.model_validate(closing)


@router.get(
    "/clients/{client_id}/fiscal-years/{year_id}/closing",
    response_model=YearClosingOut,
)
async def get_year_closing(
    client_id: uuid.UUID,
    year_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> YearClosingOut:
    await _get_client_or_404(db, client_id)
    await _get_fiscal_year_or_404(db, client_id, year_id)

    closing = await balance_sheet_service.get_year_closing(db, year_id)
    if not closing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chiusura esercizio non trovata",
        )
    return YearClosingOut.model_validate(closing)
