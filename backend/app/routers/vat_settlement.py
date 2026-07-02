"""
Router — Liquidazione IVA periodica.
"""
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.auth import User
from app.schemas.tax import (
    VatSettlementCreate,
    VatSettlementOut,
    MarkVersataSettlementIn,
    F24ProspettoOut,
    F24Riga,
)
from app.services import vat_settlement_service, parties_service

router = APIRouter(prefix="/api/v1", tags=["Liquidazione IVA"])


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


async def _get_settlement_or_404(db, client_id, year_id, settlement_id):
    s = await vat_settlement_service.get_settlement(db, client_id, year_id, settlement_id)
    if not s:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Liquidazione non trovata")
    return s


@router.post(
    "/clients/{client_id}/fiscal-years/{year_id}/vat-settlements/compute",
    response_model=VatSettlementOut,
    status_code=status.HTTP_200_OK,
)
async def compute_settlement(
    client_id: uuid.UUID,
    year_id: uuid.UUID,
    body: VatSettlementCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> VatSettlementOut:
    await _get_client_or_404(db, client_id)
    await _get_fiscal_year_or_404(db, client_id, year_id)

    settlement = await vat_settlement_service.compute_settlement(
        db,
        client_entity_id=client_id,
        fiscal_year_id=year_id,
        periodo=body.periodo,
        credito_precedente=body.credito_precedente,
    )
    return VatSettlementOut.model_validate(settlement)


@router.get(
    "/clients/{client_id}/fiscal-years/{year_id}/vat-settlements",
    response_model=List[VatSettlementOut],
)
async def list_settlements(
    client_id: uuid.UUID,
    year_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[VatSettlementOut]:
    await _get_client_or_404(db, client_id)
    await _get_fiscal_year_or_404(db, client_id, year_id)

    settlements = await vat_settlement_service.get_settlements(db, client_id, year_id)
    return [VatSettlementOut.model_validate(s) for s in settlements]


@router.get(
    "/clients/{client_id}/fiscal-years/{year_id}/vat-settlements/{settlement_id}",
    response_model=VatSettlementOut,
)
async def get_settlement(
    client_id: uuid.UUID,
    year_id: uuid.UUID,
    settlement_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> VatSettlementOut:
    await _get_client_or_404(db, client_id)
    await _get_fiscal_year_or_404(db, client_id, year_id)
    settlement = await _get_settlement_or_404(db, client_id, year_id, settlement_id)
    return VatSettlementOut.model_validate(settlement)


@router.post(
    "/clients/{client_id}/fiscal-years/{year_id}/vat-settlements/{settlement_id}/confirm",
    response_model=VatSettlementOut,
)
async def confirm_settlement(
    client_id: uuid.UUID,
    year_id: uuid.UUID,
    settlement_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> VatSettlementOut:
    await _get_client_or_404(db, client_id)
    await _get_fiscal_year_or_404(db, client_id, year_id)
    settlement = await _get_settlement_or_404(db, client_id, year_id, settlement_id)

    settlement = await vat_settlement_service.confirm_settlement(db, settlement)
    return VatSettlementOut.model_validate(settlement)


@router.post(
    "/clients/{client_id}/fiscal-years/{year_id}/vat-settlements/{settlement_id}/mark-versata",
    response_model=VatSettlementOut,
)
async def mark_versata(
    client_id: uuid.UUID,
    year_id: uuid.UUID,
    settlement_id: uuid.UUID,
    body: MarkVersataSettlementIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> VatSettlementOut:
    await _get_client_or_404(db, client_id)
    await _get_fiscal_year_or_404(db, client_id, year_id)
    settlement = await _get_settlement_or_404(db, client_id, year_id, settlement_id)

    settlement = await vat_settlement_service.mark_versata(
        db, settlement, body.data_versamento, body.f24_riferimento
    )
    return VatSettlementOut.model_validate(settlement)


@router.get(
    "/clients/{client_id}/fiscal-years/{year_id}/vat-settlements/{settlement_id}/f24",
    response_model=F24ProspettoOut,
)
async def get_f24(
    client_id: uuid.UUID,
    year_id: uuid.UUID,
    settlement_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> F24ProspettoOut:
    await _get_client_or_404(db, client_id)
    await _get_fiscal_year_or_404(db, client_id, year_id)
    settlement = await _get_settlement_or_404(db, client_id, year_id, settlement_id)

    prospetto = await vat_settlement_service.get_f24_prospetto(
        db, client_id, year_id, settlement.periodo
    )
    sezione_erario = [F24Riga(**r) for r in prospetto["sezione_erario"]]
    sezione_contributi = [F24Riga(**r) for r in prospetto["sezione_contributi"]]

    return F24ProspettoOut(
        periodo=prospetto["periodo"],
        tipo_periodo=prospetto["tipo_periodo"],
        sezione_erario=sezione_erario,
        sezione_contributi=sezione_contributi,
        totale_saldo=prospetto["totale_saldo"],
    )
