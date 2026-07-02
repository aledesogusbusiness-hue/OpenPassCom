"""
Bank Service — Riconciliazione bancaria.

Regole:
- await db.flush(), MAI await db.commit()
- await db.refresh(obj) dopo flush
"""
import uuid
from decimal import Decimal
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.bank import BankStatement, BankTransaction
from app.schemas.bank import BankStatementCreate, BankTransactionCreate

STUDIO_UUID = uuid.UUID(settings.STUDIO_ID)


async def create_bank_statement(
    db: AsyncSession,
    client_entity_id: uuid.UUID,
    data: BankStatementCreate,
    created_by: Optional[uuid.UUID] = None,
) -> BankStatement:
    stmt = BankStatement(
        id=uuid.uuid4(),
        studio_id=STUDIO_UUID,
        client_entity_id=client_entity_id,
        iban=data.iban,
        data_inizio=data.data_inizio,
        data_fine=data.data_fine,
        saldo_iniziale=data.saldo_iniziale,
        saldo_finale=data.saldo_finale,
        filename=data.filename,
        created_by=created_by,
    )
    db.add(stmt)
    await db.flush()
    await db.refresh(stmt)
    return stmt


async def list_bank_statements(
    db: AsyncSession,
    client_entity_id: uuid.UUID,
) -> List[BankStatement]:
    result = await db.execute(
        select(BankStatement).where(
            BankStatement.studio_id == STUDIO_UUID,
            BankStatement.client_entity_id == client_entity_id,
        ).order_by(BankStatement.data_inizio.desc())
    )
    return list(result.scalars().all())


async def import_transactions(
    db: AsyncSession,
    statement_id: uuid.UUID,
    transactions: List[BankTransactionCreate],
) -> List[BankTransaction]:
    """Importa le transazioni nell'estratto conto."""
    created = []
    for tx_data in transactions:
        tx = BankTransaction(
            id=uuid.uuid4(),
            studio_id=STUDIO_UUID,
            bank_statement_id=statement_id,
            data_valuta=tx_data.data_valuta,
            data_contabile=tx_data.data_contabile,
            descrizione=tx_data.descrizione,
            importo=tx_data.importo,
            tipo=tx_data.tipo,
            stato_riconciliazione="da_riconciliare",
            note=tx_data.note,
        )
        db.add(tx)
        created.append(tx)
    await db.flush()
    for tx in created:
        await db.refresh(tx)
    return created


async def list_transactions(
    db: AsyncSession,
    statement_id: uuid.UUID,
    stato: Optional[str] = None,
) -> List[BankTransaction]:
    q = select(BankTransaction).where(
        BankTransaction.studio_id == STUDIO_UUID,
        BankTransaction.bank_statement_id == statement_id,
    )
    if stato is not None:
        q = q.where(BankTransaction.stato_riconciliazione == stato)
    q = q.order_by(BankTransaction.data_contabile)
    result = await db.execute(q)
    return list(result.scalars().all())


async def get_transaction(
    db: AsyncSession,
    statement_id: uuid.UUID,
    tx_id: uuid.UUID,
) -> Optional[BankTransaction]:
    result = await db.execute(
        select(BankTransaction).where(
            BankTransaction.id == tx_id,
            BankTransaction.studio_id == STUDIO_UUID,
            BankTransaction.bank_statement_id == statement_id,
        )
    )
    return result.scalar_one_or_none()


async def reconcile_transaction(
    db: AsyncSession,
    transaction: BankTransaction,
    journal_entry_id: Optional[uuid.UUID] = None,
    scheduled_payment_id: Optional[uuid.UUID] = None,
    note: Optional[str] = None,
) -> BankTransaction:
    """
    Riconcilia una transazione con un JournalEntry o ScheduledPayment.
    Almeno uno tra journal_entry_id e scheduled_payment_id deve essere presente.
    """
    if journal_entry_id is None and scheduled_payment_id is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Almeno uno tra journal_entry_id e scheduled_payment_id deve essere fornito",
        )
    transaction.stato_riconciliazione = "riconciliata"
    transaction.journal_entry_id = journal_entry_id
    transaction.scheduled_payment_id = scheduled_payment_id
    if note is not None:
        transaction.note = note
    await db.flush()
    await db.refresh(transaction)
    return transaction


async def mark_irrilevante(
    db: AsyncSession,
    transaction: BankTransaction,
) -> BankTransaction:
    transaction.stato_riconciliazione = "irrilevante"
    await db.flush()
    await db.refresh(transaction)
    return transaction


async def get_reconciliation_summary(
    db: AsyncSession,
    statement_id: uuid.UUID,
) -> dict:
    """
    Returns: {
        totale, riconciliate, da_riconciliare, irrilevanti, saldo_riconciliato
    }
    """
    r = await db.execute(
        select(func.count(BankTransaction.id)).where(
            BankTransaction.studio_id == STUDIO_UUID,
            BankTransaction.bank_statement_id == statement_id,
        )
    )
    totale = r.scalar() or 0

    r = await db.execute(
        select(func.count(BankTransaction.id)).where(
            BankTransaction.studio_id == STUDIO_UUID,
            BankTransaction.bank_statement_id == statement_id,
            BankTransaction.stato_riconciliazione == "riconciliata",
        )
    )
    riconciliate = r.scalar() or 0

    r = await db.execute(
        select(func.count(BankTransaction.id)).where(
            BankTransaction.studio_id == STUDIO_UUID,
            BankTransaction.bank_statement_id == statement_id,
            BankTransaction.stato_riconciliazione == "da_riconciliare",
        )
    )
    da_riconciliare = r.scalar() or 0

    r = await db.execute(
        select(func.count(BankTransaction.id)).where(
            BankTransaction.studio_id == STUDIO_UUID,
            BankTransaction.bank_statement_id == statement_id,
            BankTransaction.stato_riconciliazione == "irrilevante",
        )
    )
    irrilevanti = r.scalar() or 0

    r = await db.execute(
        select(func.sum(BankTransaction.importo)).where(
            BankTransaction.studio_id == STUDIO_UUID,
            BankTransaction.bank_statement_id == statement_id,
            BankTransaction.stato_riconciliazione == "riconciliata",
        )
    )
    saldo_raw = r.scalar()
    saldo_riconciliato = Decimal(str(saldo_raw)) if saldo_raw is not None else Decimal("0")

    return {
        "totale": totale,
        "riconciliate": riconciliate,
        "da_riconciliare": da_riconciliare,
        "irrilevanti": irrilevanti,
        "saldo_riconciliato": saldo_riconciliato,
    }
