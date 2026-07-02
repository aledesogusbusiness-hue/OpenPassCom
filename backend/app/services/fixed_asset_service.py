"""
Fixed Asset Service — Cespiti e piani di ammortamento.

Regole:
- Usa Decimal per tutti i calcoli monetari con quantize(Decimal('0.01'), ROUND_HALF_UP)
- Regola del semestre: anno 1 quote_costanti → quota = costo * aliquota / 100 * 0.5
- Non sovrascrivere DepreciationEntry già 'contabilizzate'
- await db.flush() + await db.refresh(obj), MAI await db.commit()
"""
import uuid
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.balance import FixedAsset, DepreciationEntry
from app.schemas.balance import FixedAssetCreate

STUDIO_UUID = uuid.UUID(settings.STUDIO_ID)

_Q = Decimal("0.01")
_ZERO = Decimal("0")
_HALF = Decimal("0.5")
_TWO = Decimal("2")
_HUNDRED = Decimal("100")


def _d(value) -> Decimal:
    """Converti un valore SQL/float/None in Decimal."""
    if value is None:
        return _ZERO
    return Decimal(str(value))


async def create_fixed_asset(
    db: AsyncSession,
    client_entity_id: uuid.UUID,
    data: FixedAssetCreate,
    created_by: uuid.UUID,
) -> FixedAsset:
    asset = FixedAsset(
        id=uuid.uuid4(),
        studio_id=STUDIO_UUID,
        client_entity_id=client_entity_id,
        fiscal_year_acquisto=data.data_acquisto.year,
        codice=data.codice,
        descrizione=data.descrizione,
        categoria=data.categoria,
        costo_storico=data.costo_storico,
        data_acquisto=data.data_acquisto,
        account_id=data.account_id,
        aliquota_ammortamento=data.aliquota_ammortamento,
        metodo=data.metodo,
        is_active=True,
        note=data.note,
        created_by=created_by,
    )
    db.add(asset)
    await db.flush()
    await db.refresh(asset)
    return asset


async def list_fixed_assets(
    db: AsyncSession,
    client_entity_id: uuid.UUID,
    include_inactive: bool = False,
) -> List[FixedAsset]:
    query = select(FixedAsset).where(
        FixedAsset.client_entity_id == client_entity_id,
        FixedAsset.studio_id == STUDIO_UUID,
    )
    if not include_inactive:
        query = query.where(FixedAsset.is_active == True)  # noqa: E712
    query = query.order_by(FixedAsset.codice)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_fixed_asset(
    db: AsyncSession,
    asset_id: uuid.UUID,
    client_entity_id: uuid.UUID,
) -> Optional[FixedAsset]:
    result = await db.execute(
        select(FixedAsset).where(
            FixedAsset.id == asset_id,
            FixedAsset.client_entity_id == client_entity_id,
            FixedAsset.studio_id == STUDIO_UUID,
        )
    )
    return result.scalar_one_or_none()


async def deactivate_fixed_asset(
    db: AsyncSession,
    asset: FixedAsset,
) -> FixedAsset:
    asset.is_active = False
    await db.flush()
    return asset


async def compute_depreciation_plan(
    db: AsyncSession,
    asset: FixedAsset,
    anni: int = 10,
) -> List[DepreciationEntry]:
    """
    Calcola/ricalcola il piano di ammortamento per N anni.

    Quote costanti:
      - Anno 1: quota = costo_storico * aliquota% * 0.5  (regola del semestre)
      - Anni successivi: quota = costo_storico * aliquota%
      - Stop quando valore_netto_finale <= 0

    Quote decrescenti (double declining):
      - quota = valore_iniziale * aliquota% * 2
      - Quando quota >= valore_iniziale → quota = valore_iniziale (ultimo anno)

    Non sovrascrive DepreciationEntry già 'contabilizzate'.
    """
    # Carica entries esistenti
    result = await db.execute(
        select(DepreciationEntry)
        .where(DepreciationEntry.fixed_asset_id == asset.id)
        .order_by(DepreciationEntry.anno)
    )
    existing: dict[int, DepreciationEntry] = {
        e.anno: e for e in result.scalars().all()
    }

    costo_storico = _d(asset.costo_storico)
    aliquota_pct = _d(asset.aliquota_ammortamento)
    anno_inizio = asset.fiscal_year_acquisto

    fondo = _ZERO  # fondo ammortamento cumulato
    entries: List[DepreciationEntry] = []

    for i in range(anni):
        anno = anno_inizio + i

        # Preserva entries già contabilizzate
        if anno in existing and existing[anno].stato == "contabilizzato":
            e = existing[anno]
            fondo = _d(e.fondo_ammortamento)
            entries.append(e)
            continue

        valore_iniziale = costo_storico - fondo
        if valore_iniziale <= _ZERO:
            break

        # Calcolo quota
        if asset.metodo == "decrescente":
            quota = (valore_iniziale * aliquota_pct / _HUNDRED * _TWO).quantize(
                _Q, rounding=ROUND_HALF_UP
            )
        else:  # quote_costanti (default)
            quota_piena = (costo_storico * aliquota_pct / _HUNDRED).quantize(
                _Q, rounding=ROUND_HALF_UP
            )
            if i == 0:
                quota = (quota_piena * _HALF).quantize(_Q, rounding=ROUND_HALF_UP)
            else:
                quota = quota_piena

        # Clamp: la quota non può superare il valore residuo
        if quota >= valore_iniziale:
            quota = valore_iniziale.quantize(_Q, rounding=ROUND_HALF_UP)

        fondo_new = (fondo + quota).quantize(_Q, rounding=ROUND_HALF_UP)
        valore_netto_finale = (costo_storico - fondo_new).quantize(
            _Q, rounding=ROUND_HALF_UP
        )
        valore_iniziale_q = valore_iniziale.quantize(_Q, rounding=ROUND_HALF_UP)

        if anno in existing:
            # Aggiorna entry calcolata esistente
            e = existing[anno]
            e.valore_iniziale = valore_iniziale_q
            e.quota_ammortamento = quota
            e.fondo_ammortamento = fondo_new
            e.valore_netto_finale = valore_netto_finale
        else:
            e = DepreciationEntry(
                id=uuid.uuid4(),
                studio_id=asset.studio_id,
                fixed_asset_id=asset.id,
                anno=anno,
                valore_iniziale=valore_iniziale_q,
                quota_ammortamento=quota,
                fondo_ammortamento=fondo_new,
                valore_netto_finale=valore_netto_finale,
                stato="calcolato",
            )
            db.add(e)

        entries.append(e)
        fondo = fondo_new

        if valore_netto_finale <= _ZERO:
            break

    await db.flush()
    return entries


async def get_depreciation_plan(
    db: AsyncSession,
    asset_id: uuid.UUID,
) -> List[DepreciationEntry]:
    result = await db.execute(
        select(DepreciationEntry)
        .where(DepreciationEntry.fixed_asset_id == asset_id)
        .order_by(DepreciationEntry.anno)
    )
    return list(result.scalars().all())


async def book_depreciation(
    db: AsyncSession,
    entry: DepreciationEntry,
    journal_entry_id: uuid.UUID,
) -> DepreciationEntry:
    """Imposta stato='contabilizzato' e collega il journal_entry_id."""
    entry.stato = "contabilizzato"
    entry.journal_entry_id = journal_entry_id
    await db.flush()
    return entry


async def get_registro_cespiti(
    db: AsyncSession,
    client_entity_id: uuid.UUID,
    anno: int,
) -> List[dict]:
    """
    Registro cespiti per anno: per ogni cespite attivo mostra
    quota di ammortamento, fondo cumulato e valore netto dell'anno.
    """
    assets_result = await db.execute(
        select(FixedAsset).where(
            FixedAsset.client_entity_id == client_entity_id,
            FixedAsset.studio_id == STUDIO_UUID,
            FixedAsset.is_active == True,  # noqa: E712
        ).order_by(FixedAsset.codice)
    )
    assets = list(assets_result.scalars().all())

    if not assets:
        return []

    asset_ids = [a.id for a in assets]
    entries_result = await db.execute(
        select(DepreciationEntry).where(
            DepreciationEntry.fixed_asset_id.in_(asset_ids),
            DepreciationEntry.anno == anno,
        )
    )
    entry_map: dict[uuid.UUID, DepreciationEntry] = {
        e.fixed_asset_id: e for e in entries_result.scalars().all()
    }

    rows = []
    for asset in assets:
        entry = entry_map.get(asset.id)
        rows.append({
            "asset": asset,
            "quota_anno": _d(entry.quota_ammortamento) if entry else None,
            "fondo_cumulato": _d(entry.fondo_ammortamento) if entry else None,
            "valore_netto": _d(entry.valore_netto_finale) if entry else None,
        })
    return rows
