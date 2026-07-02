"""
Withholding Service — Ritenute d'acconto.
"""
import uuid
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.tax import WithholdingTax
from app.schemas.tax import WithholdingTaxCreate

STUDIO_UUID = uuid.UUID(settings.STUDIO_ID)
TWO_PLACES = Decimal("0.01")


async def create_withholding(
    db: AsyncSession,
    client_entity_id: uuid.UUID,
    fiscal_year_id: uuid.UUID,
    data: WithholdingTaxCreate,
    created_by: Optional[uuid.UUID] = None,
) -> WithholdingTax:
    """
    Crea una ritenuta d'acconto.
    importo_ritenuta = imponibile * aliquota_pct / 100 (arrotondato a 2 decimali).
    """
    importo_ritenuta = (
        data.imponibile * data.aliquota_pct / Decimal("100")
    ).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

    wt = WithholdingTax(
        id=uuid.uuid4(),
        studio_id=STUDIO_UUID,
        client_entity_id=client_entity_id,
        fiscal_year_id=fiscal_year_id,
        journal_entry_id=data.journal_entry_id,
        tipo=data.tipo,
        codice_tributo=data.codice_tributo,
        imponibile=data.imponibile,
        aliquota_pct=data.aliquota_pct,
        importo_ritenuta=importo_ritenuta,
        mese_competenza=data.mese_competenza,
        anno_competenza=data.anno_competenza,
        stato="da_versare",
    )
    db.add(wt)
    await db.flush()
    await db.refresh(wt)
    return wt


async def mark_versata(
    db: AsyncSession,
    wt: WithholdingTax,
    data_versamento: date,
    f24_riferimento: Optional[str] = None,
) -> WithholdingTax:
    """Marca la ritenuta come versata."""
    wt.stato = "versata"
    wt.data_versamento = data_versamento
    if f24_riferimento is not None:
        wt.f24_riferimento = f24_riferimento
    await db.flush()
    await db.refresh(wt)
    return wt


async def get_withholdings(
    db: AsyncSession,
    client_entity_id: uuid.UUID,
    fiscal_year_id: uuid.UUID,
    stato: Optional[str] = None,
) -> List[WithholdingTax]:
    """Lista ritenute per cliente/esercizio, con filtro opzionale per stato."""
    query = select(WithholdingTax).where(
        WithholdingTax.studio_id == STUDIO_UUID,
        WithholdingTax.client_entity_id == client_entity_id,
        WithholdingTax.fiscal_year_id == fiscal_year_id,
    )
    if stato is not None:
        query = query.where(WithholdingTax.stato == stato)
    query = query.order_by(WithholdingTax.anno_competenza, WithholdingTax.mese_competenza)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_withholding(
    db: AsyncSession,
    client_entity_id: uuid.UUID,
    fiscal_year_id: uuid.UUID,
    wt_id: uuid.UUID,
) -> Optional[WithholdingTax]:
    result = await db.execute(
        select(WithholdingTax).where(
            WithholdingTax.id == wt_id,
            WithholdingTax.studio_id == STUDIO_UUID,
            WithholdingTax.client_entity_id == client_entity_id,
            WithholdingTax.fiscal_year_id == fiscal_year_id,
        )
    )
    return result.scalar_one_or_none()


async def get_f24_ritenute(
    db: AsyncSession,
    client_entity_id: uuid.UUID,
    fiscal_year_id: uuid.UUID,
    mese: int,
    anno: int,
) -> dict:
    """
    Prospetto F24 ritenute per mese/anno.
    Raggruppa per codice_tributo sommando gli importi da_versare.
    """
    result = await db.execute(
        select(WithholdingTax).where(
            WithholdingTax.studio_id == STUDIO_UUID,
            WithholdingTax.client_entity_id == client_entity_id,
            WithholdingTax.fiscal_year_id == fiscal_year_id,
            WithholdingTax.mese_competenza == mese,
            WithholdingTax.anno_competenza == anno,
            WithholdingTax.stato == "da_versare",
        )
    )
    ritenute = list(result.scalars().all())

    # Raggruppa per codice_tributo
    aggregato: dict[str, Decimal] = {}
    for r in ritenute:
        importo = Decimal(str(r.importo_ritenuta))
        aggregato[r.codice_tributo] = aggregato.get(r.codice_tributo, Decimal("0")) + importo

    righe = [
        {"codice_tributo": codice, "importo": importo}
        for codice, importo in sorted(aggregato.items())
    ]
    totale = sum(r["importo"] for r in righe) if righe else Decimal("0")

    return {
        "mese": mese,
        "anno": anno,
        "righe": righe,
        "totale": totale,
    }
