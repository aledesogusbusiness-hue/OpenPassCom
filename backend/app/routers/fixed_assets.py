"""
Router — Cespiti e piani di ammortamento.
"""
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.auth import User
from app.schemas.balance import (
    FixedAssetCreate,
    FixedAssetOut,
    DepreciationEntryOut,
    RegistroCespiteRow,
)
from app.services import fixed_asset_service, parties_service

router = APIRouter(prefix="/api/v1", tags=["Cespiti"])


async def _get_client_or_404(db: AsyncSession, client_id: uuid.UUID):
    client = await parties_service.get_client(db, client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente non trovato",
        )
    return client


async def _get_asset_or_404(
    db: AsyncSession, asset_id: uuid.UUID, client_id: uuid.UUID
):
    asset = await fixed_asset_service.get_fixed_asset(db, asset_id, client_id)
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cespite non trovato",
        )
    return asset


# ── Cespiti CRUD ──────────────────────────────────────────────────────────────

@router.post(
    "/clients/{client_id}/fixed-assets",
    response_model=FixedAssetOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_fixed_asset(
    client_id: uuid.UUID,
    body: FixedAssetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FixedAssetOut:
    await _get_client_or_404(db, client_id)
    asset = await fixed_asset_service.create_fixed_asset(
        db, client_id, body, current_user.id
    )
    return FixedAssetOut.model_validate(asset)


@router.get(
    "/clients/{client_id}/fixed-assets",
    response_model=List[FixedAssetOut],
)
async def list_fixed_assets(
    client_id: uuid.UUID,
    include_inactive: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[FixedAssetOut]:
    await _get_client_or_404(db, client_id)
    assets = await fixed_asset_service.list_fixed_assets(
        db, client_id, include_inactive=include_inactive
    )
    return [FixedAssetOut.model_validate(a) for a in assets]


@router.get(
    "/clients/{client_id}/fixed-assets/{asset_id}",
    response_model=FixedAssetOut,
)
async def get_fixed_asset(
    client_id: uuid.UUID,
    asset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FixedAssetOut:
    await _get_client_or_404(db, client_id)
    asset = await _get_asset_or_404(db, asset_id, client_id)
    return FixedAssetOut.model_validate(asset)


@router.delete(
    "/clients/{client_id}/fixed-assets/{asset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def deactivate_fixed_asset(
    client_id: uuid.UUID,
    asset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    await _get_client_or_404(db, client_id)
    asset = await _get_asset_or_404(db, asset_id, client_id)
    await fixed_asset_service.deactivate_fixed_asset(db, asset)


# ── Piano di ammortamento ─────────────────────────────────────────────────────

@router.post(
    "/clients/{client_id}/fixed-assets/{asset_id}/compute-plan",
    response_model=List[DepreciationEntryOut],
)
async def compute_depreciation_plan(
    client_id: uuid.UUID,
    asset_id: uuid.UUID,
    anni: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[DepreciationEntryOut]:
    await _get_client_or_404(db, client_id)
    asset = await _get_asset_or_404(db, asset_id, client_id)
    entries = await fixed_asset_service.compute_depreciation_plan(db, asset, anni=anni)
    return [DepreciationEntryOut.model_validate(e) for e in entries]


@router.get(
    "/clients/{client_id}/fixed-assets/{asset_id}/plan",
    response_model=List[DepreciationEntryOut],
)
async def get_depreciation_plan(
    client_id: uuid.UUID,
    asset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[DepreciationEntryOut]:
    await _get_client_or_404(db, client_id)
    asset = await _get_asset_or_404(db, asset_id, client_id)
    entries = await fixed_asset_service.get_depreciation_plan(db, asset.id)
    return [DepreciationEntryOut.model_validate(e) for e in entries]


# ── Registro cespiti ──────────────────────────────────────────────────────────

@router.get(
    "/clients/{client_id}/registro-cespiti",
    response_model=List[RegistroCespiteRow],
)
async def get_registro_cespiti(
    client_id: uuid.UUID,
    anno: int = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[RegistroCespiteRow]:
    await _get_client_or_404(db, client_id)
    rows = await fixed_asset_service.get_registro_cespiti(db, client_id, anno)
    return [
        RegistroCespiteRow(
            asset=FixedAssetOut.model_validate(r["asset"]),
            quota_anno=r["quota_anno"],
            fondo_cumulato=r["fondo_cumulato"],
            valore_netto=r["valore_netto"],
        )
        for r in rows
    ]
