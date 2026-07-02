"""
Conservatore Service — Gestione invio documenti al conservatore digitale.

Regole:
- await db.flush(), MAI await db.commit()
- await db.refresh(obj) dopo flush
"""
import uuid
from datetime import date
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.bank import ConservatoreLog
from app.schemas.bank import ConservatoreLogCreate

STUDIO_UUID = uuid.UUID(settings.STUDIO_ID)


async def create_log(
    db: AsyncSession,
    client_entity_id: uuid.UUID,
    data: ConservatoreLogCreate,
    created_by: Optional[uuid.UUID] = None,
) -> ConservatoreLog:
    log = ConservatoreLog(
        id=uuid.uuid4(),
        studio_id=STUDIO_UUID,
        client_entity_id=client_entity_id,
        tipo_documento=data.tipo_documento,
        fiscal_year_id=data.fiscal_year_id,
        periodo=data.periodo,
        stato="da_inviare",
        note=data.note,
        created_by=created_by,
    )
    db.add(log)
    await db.flush()
    await db.refresh(log)
    return log


async def list_logs(
    db: AsyncSession,
    client_entity_id: uuid.UUID,
    stato: Optional[str] = None,
) -> List[ConservatoreLog]:
    q = select(ConservatoreLog).where(
        ConservatoreLog.studio_id == STUDIO_UUID,
        ConservatoreLog.client_entity_id == client_entity_id,
    )
    if stato is not None:
        q = q.where(ConservatoreLog.stato == stato)
    q = q.order_by(ConservatoreLog.created_at.desc())
    result = await db.execute(q)
    return list(result.scalars().all())


async def get_log(
    db: AsyncSession,
    client_entity_id: uuid.UUID,
    log_id: uuid.UUID,
) -> Optional[ConservatoreLog]:
    result = await db.execute(
        select(ConservatoreLog).where(
            ConservatoreLog.id == log_id,
            ConservatoreLog.studio_id == STUDIO_UUID,
            ConservatoreLog.client_entity_id == client_entity_id,
        )
    )
    return result.scalar_one_or_none()


async def mark_inviato(
    db: AsyncSession,
    log: ConservatoreLog,
    data_invio: date,
    riferimento: Optional[str] = None,
) -> ConservatoreLog:
    if log.stato != "da_inviare":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Solo i log in stato 'da_inviare' possono essere marcati inviati "
                f"(stato: {log.stato})"
            ),
        )
    log.stato = "inviato"
    log.data_invio = data_invio
    if riferimento is not None:
        log.riferimento_esterno = riferimento
    await db.flush()
    await db.refresh(log)
    return log


async def mark_confermato(
    db: AsyncSession,
    log: ConservatoreLog,
) -> ConservatoreLog:
    if log.stato != "inviato":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Solo i log in stato 'inviato' possono essere confermati "
                f"(stato: {log.stato})"
            ),
        )
    log.stato = "confermato"
    await db.flush()
    await db.refresh(log)
    return log


async def mark_errore(
    db: AsyncSession,
    log: ConservatoreLog,
    note: str,
) -> ConservatoreLog:
    log.stato = "errore"
    log.note = note
    await db.flush()
    await db.refresh(log)
    return log
