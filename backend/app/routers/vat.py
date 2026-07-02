"""
Router — Registro IVA e liquidazione.
"""
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.auth import User
from app.schemas.journal import VatEntryCreate, VatEntryOut, VatLiquidazioneOut
from app.services import vat_service, parties_service

router = APIRouter(prefix="/api/v1", tags=["Registro IVA"])


async def _get_client_or_404(db: AsyncSession, client_id: uuid.UUID):
    client = await parties_service.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente non trovato")
    return client


async def _get_fiscal_year_or_404(db: AsyncSession, client_id: uuid.UUID, year_id: uuid.UUID):
    fy = await parties_service.get_fiscal_year(db, client_id, year_id)
    if not fy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Esercizio fiscale non trovato")
    return fy


@router.get(
    "/clients/{client_id}/fiscal-years/{year_id}/vat/vendite",
    response_model=List[VatEntryOut],
)
async def get_vat_vendite(
    client_id: uuid.UUID,
    year_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[VatEntryOut]:
    await _get_client_or_404(db, client_id)
    await _get_fiscal_year_or_404(db, client_id, year_id)

    entries = await vat_service.get_vat_entries(db, client_id, year_id, "vendite")
    return [VatEntryOut.model_validate(e) for e in entries]


@router.get(
    "/clients/{client_id}/fiscal-years/{year_id}/vat/acquisti",
    response_model=List[VatEntryOut],
)
async def get_vat_acquisti(
    client_id: uuid.UUID,
    year_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[VatEntryOut]:
    await _get_client_or_404(db, client_id)
    await _get_fiscal_year_or_404(db, client_id, year_id)

    entries = await vat_service.get_vat_entries(db, client_id, year_id, "acquisti")
    return [VatEntryOut.model_validate(e) for e in entries]


@router.post(
    "/clients/{client_id}/fiscal-years/{year_id}/vat/entries",
    response_model=VatEntryOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_vat_entry(
    client_id: uuid.UUID,
    year_id: uuid.UUID,
    body: VatEntryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> VatEntryOut:
    await _get_client_or_404(db, client_id)
    await _get_fiscal_year_or_404(db, client_id, year_id)

    entry = await vat_service.create_vat_entry(db, client_id, year_id, body)
    return VatEntryOut.model_validate(entry)


@router.get(
    "/clients/{client_id}/fiscal-years/{year_id}/vat/liquidazione",
    response_model=VatLiquidazioneOut,
)
async def get_vat_liquidazione(
    client_id: uuid.UUID,
    year_id: uuid.UUID,
    periodo: str = Query(..., description="Es. '2024-03' mensile o '2024-Q1' trimestrale"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> VatLiquidazioneOut:
    await _get_client_or_404(db, client_id)
    await _get_fiscal_year_or_404(db, client_id, year_id)

    return await vat_service.get_vat_liquidazione(db, client_id, year_id, periodo)
