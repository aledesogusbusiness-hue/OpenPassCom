"""
VAT Service — Registro IVA e liquidazione.

Invariante 10bis: regime forfettario non può avere registrazioni IVA.
"""
import uuid
from datetime import date
from decimal import Decimal
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import select, func as sqlfunc
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.journal import VatRegister, VatEntry
from app.models.parties import ClientEntity, FiscalYear
from app.schemas.journal import VatEntryCreate, VatEntryOut, VatLiquidazioneOut

STUDIO_UUID = uuid.UUID(settings.STUDIO_ID)


def _to_decimal(value) -> Decimal:
    if value is None:
        return Decimal("0")
    return Decimal(str(value))


async def _get_client(db: AsyncSession, client_entity_id: uuid.UUID) -> Optional[ClientEntity]:
    result = await db.execute(
        select(ClientEntity).where(
            ClientEntity.id == client_entity_id,
            ClientEntity.studio_id == STUDIO_UUID,
        )
    )
    return result.scalar_one_or_none()


async def get_or_create_vat_register(
    db: AsyncSession,
    client_entity_id: uuid.UUID,
    fiscal_year_id: uuid.UUID,
    tipo: str,
) -> VatRegister:
    """Recupera o crea il registro IVA per tipo (vendite|acquisti)."""
    result = await db.execute(
        select(VatRegister).where(
            VatRegister.studio_id == STUDIO_UUID,
            VatRegister.client_entity_id == client_entity_id,
            VatRegister.fiscal_year_id == fiscal_year_id,
            VatRegister.tipo == tipo,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        return existing

    register = VatRegister(
        id=uuid.uuid4(),
        studio_id=STUDIO_UUID,
        client_entity_id=client_entity_id,
        fiscal_year_id=fiscal_year_id,
        tipo=tipo,
    )
    db.add(register)
    await db.flush()
    return register


async def create_vat_entry(
    db: AsyncSession,
    client_entity_id: uuid.UUID,
    fiscal_year_id: uuid.UUID,
    data: VatEntryCreate,
) -> VatEntry:
    """
    Crea una riga nel registro IVA.
    Invariante 10bis: regime forfettario → errore 422.
    """
    client = await _get_client(db, client_entity_id)
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente non trovato")

    if client.fiscal_regime == "forfettario":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invariante 10bis: il regime forfettario non prevede registrazioni IVA",
        )

    register = await get_or_create_vat_register(db, client_entity_id, fiscal_year_id, data.tipo)

    entry = VatEntry(
        id=uuid.uuid4(),
        studio_id=STUDIO_UUID,
        vat_register_id=register.id,
        journal_entry_id=data.journal_entry_id,
        data_documento=data.data_documento,
        numero_documento=data.numero_documento,
        controparte=data.controparte,
        imponibile=data.imponibile,
        aliquota=data.aliquota,
        imposta=data.imposta,
    )
    db.add(entry)
    await db.flush()
    await db.refresh(entry)
    return entry


async def get_vat_entries(
    db: AsyncSession,
    client_entity_id: uuid.UUID,
    fiscal_year_id: uuid.UUID,
    tipo: str,
) -> List[VatEntry]:
    """Restituisce le voci del registro IVA per tipo."""
    register_result = await db.execute(
        select(VatRegister).where(
            VatRegister.studio_id == STUDIO_UUID,
            VatRegister.client_entity_id == client_entity_id,
            VatRegister.fiscal_year_id == fiscal_year_id,
            VatRegister.tipo == tipo,
        )
    )
    register = register_result.scalar_one_or_none()
    if register is None:
        return []

    result = await db.execute(
        select(VatEntry)
        .where(VatEntry.vat_register_id == register.id)
        .order_by(VatEntry.data_documento)
    )
    return list(result.scalars().all())


async def get_vat_liquidazione(
    db: AsyncSession,
    client_entity_id: uuid.UUID,
    fiscal_year_id: uuid.UUID,
    periodo: str,
) -> VatLiquidazioneOut:
    """
    Calcola liquidazione IVA per periodo.
    periodo: '2024-03' (mensile) o '2024-Q1' (trimestrale).
    """
    # Parse periodo
    if "Q" in periodo:
        # Trimestrale: '2024-Q1'
        year_str, q_str = periodo.split("-Q")
        year = int(year_str)
        q = int(q_str)
        month_start = (q - 1) * 3 + 1
        month_end = month_start + 2
    else:
        # Mensile: '2024-03'
        year_str, month_str = periodo.split("-")
        year = int(year_str)
        month_start = int(month_str)
        month_end = month_start

    date_from = date(year, month_start, 1)
    if month_end == 12:
        date_to = date(year + 1, 1, 1)
    else:
        date_to = date(year, month_end + 1, 1)

    iva_vendite = Decimal("0")
    iva_acquisti = Decimal("0")

    for tipo in ("vendite", "acquisti"):
        register_result = await db.execute(
            select(VatRegister).where(
                VatRegister.studio_id == STUDIO_UUID,
                VatRegister.client_entity_id == client_entity_id,
                VatRegister.fiscal_year_id == fiscal_year_id,
                VatRegister.tipo == tipo,
            )
        )
        register = register_result.scalar_one_or_none()
        if register is None:
            continue

        total_result = await db.execute(
            select(sqlfunc.sum(VatEntry.imposta)).where(
                VatEntry.vat_register_id == register.id,
                VatEntry.data_documento >= date_from,
                VatEntry.data_documento < date_to,
            )
        )
        total = _to_decimal(total_result.scalar())
        if tipo == "vendite":
            iva_vendite = total
        else:
            iva_acquisti = total

    return VatLiquidazioneOut(
        periodo=periodo,
        iva_vendite=iva_vendite,
        iva_acquisti=iva_acquisti,
        debito_credito=iva_vendite - iva_acquisti,
    )
