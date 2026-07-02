"""
Payment Service — Scadenzario.
"""
import uuid
from datetime import date
from decimal import Decimal
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.journal import PaymentSchedule, ScheduledPayment
from app.schemas.journal import PaymentScheduleCreate, ScheduledPaymentCreate

STUDIO_UUID = uuid.UUID(settings.STUDIO_ID)


async def create_payment_schedule(
    db: AsyncSession,
    client_entity_id: uuid.UUID,
    data: PaymentScheduleCreate,
) -> PaymentSchedule:
    schedule = PaymentSchedule(
        id=uuid.uuid4(),
        studio_id=STUDIO_UUID,
        client_entity_id=client_entity_id,
        journal_entry_id=data.journal_entry_id,
        descrizione=data.descrizione,
    )
    db.add(schedule)
    await db.flush()
    await db.refresh(schedule)
    return schedule


async def get_payment_schedule(
    db: AsyncSession,
    client_entity_id: uuid.UUID,
    schedule_id: uuid.UUID,
) -> Optional[PaymentSchedule]:
    result = await db.execute(
        select(PaymentSchedule).where(
            PaymentSchedule.id == schedule_id,
            PaymentSchedule.client_entity_id == client_entity_id,
            PaymentSchedule.studio_id == STUDIO_UUID,
        )
    )
    return result.scalar_one_or_none()


async def add_scheduled_payment(
    db: AsyncSession,
    schedule: PaymentSchedule,
    data: ScheduledPaymentCreate,
) -> ScheduledPayment:
    payment = ScheduledPayment(
        id=uuid.uuid4(),
        studio_id=STUDIO_UUID,
        payment_schedule_id=schedule.id,
        data_scadenza=data.data_scadenza,
        importo=data.importo,
        tipo=data.tipo,
        stato="aperto",
        note=data.note,
    )
    db.add(payment)
    await db.flush()
    await db.refresh(payment)
    return payment


async def get_scheduled_payment(
    db: AsyncSession,
    schedule: PaymentSchedule,
    payment_id: uuid.UUID,
) -> Optional[ScheduledPayment]:
    result = await db.execute(
        select(ScheduledPayment).where(
            ScheduledPayment.id == payment_id,
            ScheduledPayment.payment_schedule_id == schedule.id,
        )
    )
    return result.scalar_one_or_none()


async def mark_paid(
    db: AsyncSession,
    payment: ScheduledPayment,
    data_pagamento: date,
) -> ScheduledPayment:
    if payment.stato == "annullato":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La scadenza è annullata e non può essere pagata",
        )
    payment.stato = "pagato"
    payment.data_pagamento = data_pagamento
    await db.flush()
    return payment


async def get_scadenzario(
    db: AsyncSession,
    client_entity_id: uuid.UUID,
    stato: Optional[str] = None,
) -> List[ScheduledPayment]:
    """Restituisce le scadenze del cliente, opzionalmente filtrate per stato."""
    # Prima: recupera tutti gli schedule del cliente
    schedules_result = await db.execute(
        select(PaymentSchedule).where(
            PaymentSchedule.client_entity_id == client_entity_id,
            PaymentSchedule.studio_id == STUDIO_UUID,
        )
    )
    schedules = list(schedules_result.scalars().all())
    if not schedules:
        return []

    schedule_ids = [s.id for s in schedules]

    query = select(ScheduledPayment).where(
        ScheduledPayment.payment_schedule_id.in_(schedule_ids)
    )
    if stato:
        query = query.where(ScheduledPayment.stato == stato)

    query = query.order_by(ScheduledPayment.data_scadenza)
    result = await db.execute(query)
    return list(result.scalars().all())
