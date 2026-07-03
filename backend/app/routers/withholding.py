"""
Router — Ritenute d'acconto.
"""
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, verify_client_access
from app.models.auth import User
from app.schemas.tax import (
    WithholdingTaxCreate,
    WithholdingTaxOut,
    WithholdingMarkVersataIn,
    F24RitenutaOut,
    F24RitenutaRiga,
)
from app.services import withholding_service, parties_service

router = APIRouter(prefix="/api/v1", tags=["Ritenute d'acconto"], dependencies=[Depends(verify_client_access)])


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


async def _get_wt_or_404(db, client_id, year_id, wt_id):
    wt = await withholding_service.get_withholding(db, client_id, year_id, wt_id)
    if not wt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ritenuta non trovata")
    return wt


@router.post(
    "/clients/{client_id}/fiscal-years/{year_id}/withholdings",
    response_model=WithholdingTaxOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_withholding(
    client_id: uuid.UUID,
    year_id: uuid.UUID,
    body: WithholdingTaxCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WithholdingTaxOut:
    await _get_client_or_404(db, client_id)
    await _get_fiscal_year_or_404(db, client_id, year_id)

    wt = await withholding_service.create_withholding(
        db, client_id, year_id, body, created_by=current_user.id
    )
    return WithholdingTaxOut.model_validate(wt)


@router.get(
    "/clients/{client_id}/fiscal-years/{year_id}/withholdings",
    response_model=List[WithholdingTaxOut],
)
async def list_withholdings(
    client_id: uuid.UUID,
    year_id: uuid.UUID,
    stato: Optional[str] = Query(default=None, description="Filtro per stato: da_versare | versata"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[WithholdingTaxOut]:
    await _get_client_or_404(db, client_id)
    await _get_fiscal_year_or_404(db, client_id, year_id)

    wts = await withholding_service.get_withholdings(db, client_id, year_id, stato=stato)
    return [WithholdingTaxOut.model_validate(w) for w in wts]


@router.post(
    "/clients/{client_id}/fiscal-years/{year_id}/withholdings/{wt_id}/mark-versata",
    response_model=WithholdingTaxOut,
)
async def mark_versata(
    client_id: uuid.UUID,
    year_id: uuid.UUID,
    wt_id: uuid.UUID,
    body: WithholdingMarkVersataIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WithholdingTaxOut:
    await _get_client_or_404(db, client_id)
    await _get_fiscal_year_or_404(db, client_id, year_id)
    wt = await _get_wt_or_404(db, client_id, year_id, wt_id)

    wt = await withholding_service.mark_versata(db, wt, body.data_versamento, body.f24_riferimento)
    return WithholdingTaxOut.model_validate(wt)


@router.get(
    "/clients/{client_id}/fiscal-years/{year_id}/withholdings/f24",
    response_model=F24RitenutaOut,
)
async def get_f24_ritenute(
    client_id: uuid.UUID,
    year_id: uuid.UUID,
    mese: int = Query(..., ge=1, le=12, description="Mese (1-12)"),
    anno: int = Query(..., ge=2000, description="Anno"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> F24RitenutaOut:
    await _get_client_or_404(db, client_id)
    await _get_fiscal_year_or_404(db, client_id, year_id)

    prospetto = await withholding_service.get_f24_ritenute(db, client_id, year_id, mese, anno)
    righe = [F24RitenutaRiga(**r) for r in prospetto["righe"]]
    return F24RitenutaOut(
        mese=prospetto["mese"],
        anno=prospetto["anno"],
        righe=righe,
        totale=prospetto["totale"],
    )
