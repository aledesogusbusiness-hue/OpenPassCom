"""
Studio Task Service — Task management dello studio commercialista.

Regole:
- await db.flush(), MAI await db.commit()
- await db.refresh(obj) dopo flush
"""
import uuid
from datetime import date, timedelta
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.parties import ClientEntity
from app.models.journal import ScheduledPayment
from app.models.tax import VatSettlement, WithholdingTax, FatturaPAImport
from app.models.studio import StudioTask
from app.schemas.studio import StudioTaskCreate, StudioTaskUpdate

STUDIO_UUID = uuid.UUID(settings.STUDIO_ID)


async def create_task(
    db: AsyncSession,
    data: StudioTaskCreate,
    created_by: Optional[uuid.UUID] = None,
) -> StudioTask:
    task = StudioTask(
        id=uuid.uuid4(),
        studio_id=STUDIO_UUID,
        client_entity_id=data.client_entity_id,
        fiscal_year_id=data.fiscal_year_id,
        titolo=data.titolo,
        descrizione=data.descrizione,
        tipo=data.tipo,
        priorita=data.priorita,
        stato="aperto",
        data_scadenza=data.data_scadenza,
        assegnato_a=data.assegnato_a,
        note=data.note,
        created_by=created_by,
    )
    db.add(task)
    await db.flush()
    await db.refresh(task)
    return task


async def list_tasks(
    db: AsyncSession,
    stato: Optional[str] = None,
    client_entity_id: Optional[uuid.UUID] = None,
    tipo: Optional[str] = None,
) -> List[StudioTask]:
    q = select(StudioTask).where(StudioTask.studio_id == STUDIO_UUID)
    if stato is not None:
        q = q.where(StudioTask.stato == stato)
    if client_entity_id is not None:
        q = q.where(StudioTask.client_entity_id == client_entity_id)
    if tipo is not None:
        q = q.where(StudioTask.tipo == tipo)
    q = q.order_by(StudioTask.created_at.desc())
    result = await db.execute(q)
    return list(result.scalars().all())


async def get_task(db: AsyncSession, task_id: uuid.UUID) -> Optional[StudioTask]:
    result = await db.execute(
        select(StudioTask).where(
            StudioTask.id == task_id,
            StudioTask.studio_id == STUDIO_UUID,
        )
    )
    return result.scalar_one_or_none()


async def update_task(
    db: AsyncSession,
    task: StudioTask,
    data: StudioTaskUpdate,
) -> StudioTask:
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)
    await db.flush()
    await db.refresh(task)
    return task


async def complete_task(
    db: AsyncSession,
    task: StudioTask,
    completato_il: date,
) -> StudioTask:
    if task.stato != "aperto":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Solo i task in stato 'aperto' possono essere completati (stato: {task.stato})",
        )
    task.stato = "completato"
    task.completato_il = completato_il
    await db.flush()
    await db.refresh(task)
    return task


async def cancel_task(db: AsyncSession, task: StudioTask) -> StudioTask:
    if task.stato != "aperto":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Solo i task in stato 'aperto' possono essere annullati (stato: {task.stato})",
        )
    task.stato = "annullato"
    await db.flush()
    await db.refresh(task)
    return task


async def get_dashboard_summary(db: AsyncSession) -> dict:
    """Aggrega le metriche chiave dello studio."""

    # clienti_attivi
    r = await db.execute(
        select(func.count(ClientEntity.id)).where(ClientEntity.is_active == True)  # noqa: E712
    )
    clienti_attivi = r.scalar() or 0

    # task_aperti
    r = await db.execute(
        select(func.count(StudioTask.id)).where(
            StudioTask.studio_id == STUDIO_UUID,
            StudioTask.stato == "aperto",
        )
    )
    task_aperti = r.scalar() or 0

    # task_urgenti (priorita='urgente' AND stato='aperto')
    r = await db.execute(
        select(func.count(StudioTask.id)).where(
            StudioTask.studio_id == STUDIO_UUID,
            StudioTask.priorita == "urgente",
            StudioTask.stato == "aperto",
        )
    )
    task_urgenti = r.scalar() or 0

    # scadenze_questa_settimana (ScheduledPayment con data_scadenza nei prossimi 7gg AND stato='aperto')
    oggi = date.today()
    fine_settimana = oggi + timedelta(days=7)
    r = await db.execute(
        select(func.count(ScheduledPayment.id)).where(
            ScheduledPayment.studio_id == STUDIO_UUID,
            ScheduledPayment.stato == "aperto",
            ScheduledPayment.data_scadenza >= oggi,
            ScheduledPayment.data_scadenza <= fine_settimana,
        )
    )
    scadenze_questa_settimana = r.scalar() or 0

    # liquidazioni_bozza (VatSettlement con stato='bozza')
    r = await db.execute(
        select(func.count(VatSettlement.id)).where(
            VatSettlement.studio_id == STUDIO_UUID,
            VatSettlement.stato == "bozza",
        )
    )
    liquidazioni_bozza = r.scalar() or 0

    # ritenute_da_versare (WithholdingTax con stato='da_versare')
    r = await db.execute(
        select(func.count(WithholdingTax.id)).where(
            WithholdingTax.studio_id == STUDIO_UUID,
            WithholdingTax.stato == "da_versare",
        )
    )
    ritenute_da_versare = r.scalar() or 0

    # fatture_importate (FatturaPAImport con stato='importata')
    r = await db.execute(
        select(func.count(FatturaPAImport.id)).where(
            FatturaPAImport.studio_id == STUDIO_UUID,
            FatturaPAImport.stato == "importata",
        )
    )
    fatture_importate = r.scalar() or 0

    return {
        "clienti_attivi": clienti_attivi,
        "task_aperti": task_aperti,
        "task_urgenti": task_urgenti,
        "scadenze_questa_settimana": scadenze_questa_settimana,
        "liquidazioni_bozza": liquidazioni_bozza,
        "ritenute_da_versare": ritenute_da_versare,
        "fatture_importate": fatture_importate,
    }


async def generate_scadenzario_tasks(
    db: AsyncSession,
    created_by: Optional[uuid.UUID] = None,
) -> List[StudioTask]:
    """
    Genera automaticamente task per scadenze fiscali imminenti (entro 30 giorni).
    - VatSettlement bozza → task tipo='scadenza_iva'
    - ScheduledPayment aperto con data_scadenza <= oggi+30 → task tipo='generico'
    Non crea duplicati.
    """
    oggi = date.today()
    limite = oggi + timedelta(days=30)
    nuovi_task: List[StudioTask] = []

    # VatSettlement in bozza → task tipo='scadenza_iva'
    r = await db.execute(
        select(VatSettlement).where(
            VatSettlement.studio_id == STUDIO_UUID,
            VatSettlement.stato == "bozza",
        )
    )
    settlements = list(r.scalars().all())

    for vs in settlements:
        # Controlla duplicati: task aperto dello stesso tipo, stesso cliente, stesso fiscal_year
        dup_r = await db.execute(
            select(StudioTask).where(
                StudioTask.studio_id == STUDIO_UUID,
                StudioTask.tipo == "scadenza_iva",
                StudioTask.client_entity_id == vs.client_entity_id,
                StudioTask.fiscal_year_id == vs.fiscal_year_id,
                StudioTask.stato == "aperto",
            )
        )
        if dup_r.scalar_one_or_none() is not None:
            continue

        task = StudioTask(
            id=uuid.uuid4(),
            studio_id=STUDIO_UUID,
            client_entity_id=vs.client_entity_id,
            fiscal_year_id=vs.fiscal_year_id,
            titolo=f"Liquidazione IVA periodo {vs.periodo}",
            tipo="scadenza_iva",
            priorita="alta",
            stato="aperto",
            created_by=created_by,
        )
        db.add(task)
        nuovi_task.append(task)

    # ScheduledPayment aperto con data_scadenza <= oggi+30 → task tipo='generico'
    r = await db.execute(
        select(ScheduledPayment).where(
            ScheduledPayment.studio_id == STUDIO_UUID,
            ScheduledPayment.stato == "aperto",
            ScheduledPayment.data_scadenza <= limite,
        )
    )
    payments = list(r.scalars().all())

    for sp in payments:
        # Controlla duplicati: stesso tipo e stessa data_scadenza già in task aperti
        dup_r = await db.execute(
            select(StudioTask).where(
                StudioTask.studio_id == STUDIO_UUID,
                StudioTask.tipo == "generico",
                StudioTask.stato == "aperto",
                StudioTask.data_scadenza == sp.data_scadenza,
            )
        )
        if dup_r.scalar_one_or_none() is not None:
            continue

        task = StudioTask(
            id=uuid.uuid4(),
            studio_id=STUDIO_UUID,
            titolo=f"Scadenza pagamento {sp.data_scadenza}",
            tipo="generico",
            priorita="normale",
            stato="aperto",
            data_scadenza=sp.data_scadenza,
            created_by=created_by,
        )
        db.add(task)
        nuovi_task.append(task)

    if nuovi_task:
        await db.flush()
        for t in nuovi_task:
            await db.refresh(t)

    return nuovi_task
