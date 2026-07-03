"""
Router — Scadenzario (payment schedules e scadenze).
"""
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, verify_client_access
from app.models.auth import User
from app.schemas.journal import (
    PaymentScheduleCreate,
    PaymentScheduleOut,
    ScheduledPaymentCreate,
    ScheduledPaymentOut,
    MarkPaidIn,
)
from app.services import payment_service, parties_service

router = APIRouter(prefix="/api/v1", tags=["Scadenzario"], dependencies=[Depends(verify_client_access)])


async def _get_client_or_404(db: AsyncSession, client_id: uuid.UUID):
    client = await parties_service.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente non trovato")
    return client


@router.get(
    "/clients/{client_id}/scadenzario",
    response_model=List[ScheduledPaymentOut],
)
async def get_scadenzario(
    client_id: uuid.UUID,
    stato: Optional[str] = Query(None, description="Filtra per stato: aperto|pagato|annullato"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[ScheduledPaymentOut]:
    await _get_client_or_404(db, client_id)

    payments = await payment_service.get_scadenzario(db, client_id, stato)
    return [ScheduledPaymentOut.model_validate(p) for p in payments]


@router.post(
    "/clients/{client_id}/payment-schedules",
    response_model=PaymentScheduleOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_payment_schedule(
    client_id: uuid.UUID,
    body: PaymentScheduleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PaymentScheduleOut:
    await _get_client_or_404(db, client_id)

    schedule = await payment_service.create_payment_schedule(db, client_id, body)
    return PaymentScheduleOut.model_validate(schedule)


@router.post(
    "/clients/{client_id}/payment-schedules/{schedule_id}/payments",
    response_model=ScheduledPaymentOut,
    status_code=status.HTTP_201_CREATED,
)
async def add_scheduled_payment(
    client_id: uuid.UUID,
    schedule_id: uuid.UUID,
    body: ScheduledPaymentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ScheduledPaymentOut:
    await _get_client_or_404(db, client_id)

    schedule = await payment_service.get_payment_schedule(db, client_id, schedule_id)
    if not schedule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Piano di pagamento non trovato")

    payment = await payment_service.add_scheduled_payment(db, schedule, body)
    return ScheduledPaymentOut.model_validate(payment)


@router.post(
    "/clients/{client_id}/payment-schedules/{schedule_id}/payments/{payment_id}/mark-paid",
    response_model=ScheduledPaymentOut,
)
async def mark_paid(
    client_id: uuid.UUID,
    schedule_id: uuid.UUID,
    payment_id: uuid.UUID,
    body: MarkPaidIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ScheduledPaymentOut:
    await _get_client_or_404(db, client_id)

    schedule = await payment_service.get_payment_schedule(db, client_id, schedule_id)
    if not schedule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Piano di pagamento non trovato")

    payment = await payment_service.get_scheduled_payment(db, schedule, payment_id)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scadenza non trovata")

    payment = await payment_service.mark_paid(db, payment, body.data_pagamento)
    return ScheduledPaymentOut.model_validate(payment)
