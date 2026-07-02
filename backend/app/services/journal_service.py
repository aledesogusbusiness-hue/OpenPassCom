"""
Journal Service — Prima nota contabile.

Regole chiave:
- next_sequence usa SELECT FOR UPDATE su PostgreSQL; SQLite (test) usa plain SELECT
- Quadratura dare=avere verificata in post_journal_entry, NON in create
- Invariante 10bis: regime forfettario + VatEntry → errore 422
"""
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import select, func as sqlfunc
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.journal import JournalEntry, JournalLine, SequenceCounter, VatEntry
from app.models.accounting import Account
from app.models.parties import ClientEntity
from app.schemas.journal import JournalEntryCreate, JournalEntryDetail, MastrinMovimento, MastrinoOut, BilancioVoce

STUDIO_UUID = uuid.UUID(settings.STUDIO_ID)


def _to_decimal(value) -> Decimal:
    """Converte un valore SQL (può essere float/None) in Decimal."""
    if value is None:
        return Decimal("0")
    return Decimal(str(value))


async def _supports_for_update(db: AsyncSession) -> bool:
    """Verifica se il DB supporta SELECT FOR UPDATE (PostgreSQL sì, SQLite no)."""
    conn = await db.connection()
    return conn.engine.dialect.name == "postgresql"


async def next_sequence(
    db: AsyncSession,
    studio_id: uuid.UUID,
    client_entity_id: uuid.UUID,
    fiscal_year_id: uuid.UUID,
    counter_name: str = "journal",
) -> int:
    """
    Incrementa SequenceCounter in modo atomico.
    PostgreSQL: SELECT FOR UPDATE per evitare race condition.
    SQLite (test): StaticPool garantisce serializzazione implicita.
    """
    base_stmt = select(SequenceCounter).where(
        SequenceCounter.studio_id == studio_id,
        SequenceCounter.client_entity_id == client_entity_id,
        SequenceCounter.fiscal_year_id == fiscal_year_id,
        SequenceCounter.counter_name == counter_name,
    )

    if await _supports_for_update(db):
        stmt = base_stmt.with_for_update()
    else:
        stmt = base_stmt

    result = await db.execute(stmt)
    counter = result.scalar_one_or_none()

    if counter is None:
        counter = SequenceCounter(
            id=uuid.uuid4(),
            studio_id=studio_id,
            client_entity_id=client_entity_id,
            fiscal_year_id=fiscal_year_id,
            counter_name=counter_name,
            last_value=1,
        )
        db.add(counter)
        await db.flush()
        return 1

    counter.last_value += 1
    await db.flush()
    return counter.last_value


async def create_journal_entry(
    db: AsyncSession,
    client_entity_id: uuid.UUID,
    fiscal_year_id: uuid.UUID,
    data: JournalEntryCreate,
    created_by: uuid.UUID,
) -> JournalEntry:
    """
    Crea registrazione in stato 'draft' con le righe associate.
    NON verifica la quadratura — viene verificata in post_journal_entry.
    """
    numero = await next_sequence(db, STUDIO_UUID, client_entity_id, fiscal_year_id)

    entry = JournalEntry(
        id=uuid.uuid4(),
        studio_id=STUDIO_UUID,
        client_entity_id=client_entity_id,
        fiscal_year_id=fiscal_year_id,
        numero_registrazione=numero,
        data_registrazione=data.data_registrazione,
        descrizione=data.descrizione,
        causale=data.causale,
        stato="draft",
        created_by=created_by,
    )
    db.add(entry)
    await db.flush()

    for line_data in data.lines:
        line = JournalLine(
            id=uuid.uuid4(),
            studio_id=STUDIO_UUID,
            journal_entry_id=entry.id,
            account_id=line_data.account_id,
            dare=line_data.dare,
            avere=line_data.avere,
            descrizione=line_data.descrizione,
        )
        db.add(line)

    await db.flush()
    await db.refresh(entry)
    return entry


async def _get_lines(db: AsyncSession, entry_id: uuid.UUID) -> List[JournalLine]:
    result = await db.execute(
        select(JournalLine).where(JournalLine.journal_entry_id == entry_id)
    )
    return list(result.scalars().all())


async def post_journal_entry(db: AsyncSession, entry: JournalEntry) -> JournalEntry:
    """
    Porta la registrazione da 'draft' a 'posted'.
    Verifica quadratura (sum dare == sum avere).
    Verifica invariante 10bis per regime forfettario.
    """
    if entry.stato != "draft":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Solo le registrazioni in stato 'draft' possono essere contabilizzate (stato attuale: {entry.stato})",
        )

    lines = await _get_lines(db, entry.id)
    if not lines:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La registrazione non ha righe",
        )

    tot_dare = sum(_to_decimal(l.dare) for l in lines)
    tot_avere = sum(_to_decimal(l.avere) for l in lines)
    if tot_dare != tot_avere:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"La registrazione non è in pareggio: dare={tot_dare} avere={tot_avere}",
        )

    # Invariante 10bis: forfettario non può avere IVA
    client_result = await db.execute(
        select(ClientEntity).where(ClientEntity.id == entry.client_entity_id)
    )
    client = client_result.scalar_one_or_none()
    if client and client.fiscal_regime == "forfettario":
        vat_result = await db.execute(
            select(VatEntry).where(VatEntry.journal_entry_id == entry.id)
        )
        if vat_result.scalars().first() is not None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invariante 10bis: il regime forfettario non prevede registrazioni IVA",
            )

    entry.stato = "posted"
    await db.flush()
    return entry


async def reverse_journal_entry(
    db: AsyncSession,
    entry: JournalEntry,
    created_by: uuid.UUID,
) -> JournalEntry:
    """
    Crea una registrazione di storno (segni invertiti) in stato 'posted'.
    Imposta entry.stato='reversed' e entry.reversed_by=nuovo_entry.id.
    """
    if entry.stato != "posted":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Solo le registrazioni in stato 'posted' possono essere stornate",
        )

    orig_lines = await _get_lines(db, entry.id)
    new_numero = await next_sequence(db, STUDIO_UUID, entry.client_entity_id, entry.fiscal_year_id)
    today = date.today()

    new_entry = JournalEntry(
        id=uuid.uuid4(),
        studio_id=STUDIO_UUID,
        client_entity_id=entry.client_entity_id,
        fiscal_year_id=entry.fiscal_year_id,
        numero_registrazione=new_numero,
        data_registrazione=today,
        descrizione=f"Storno: {entry.descrizione}",
        causale=entry.causale,
        stato="posted",
        created_by=created_by,
    )
    db.add(new_entry)
    await db.flush()

    for orig in orig_lines:
        reversed_line = JournalLine(
            id=uuid.uuid4(),
            studio_id=orig.studio_id,
            journal_entry_id=new_entry.id,
            account_id=orig.account_id,
            dare=_to_decimal(orig.avere),   # segni invertiti
            avere=_to_decimal(orig.dare),
            descrizione=orig.descrizione,
        )
        db.add(reversed_line)

    entry.stato = "reversed"
    entry.reversed_by = new_entry.id
    await db.flush()

    return new_entry


async def get_journal_entry(
    db: AsyncSession,
    client_entity_id: uuid.UUID,
    fiscal_year_id: uuid.UUID,
    entry_id: uuid.UUID,
) -> Optional[JournalEntry]:
    result = await db.execute(
        select(JournalEntry).where(
            JournalEntry.id == entry_id,
            JournalEntry.client_entity_id == client_entity_id,
            JournalEntry.fiscal_year_id == fiscal_year_id,
            JournalEntry.studio_id == STUDIO_UUID,
        )
    )
    return result.scalar_one_or_none()


async def get_journal_entry_detail(
    db: AsyncSession,
    client_entity_id: uuid.UUID,
    fiscal_year_id: uuid.UUID,
    entry_id: uuid.UUID,
) -> Optional[JournalEntryDetail]:
    entry = await get_journal_entry(db, client_entity_id, fiscal_year_id, entry_id)
    if entry is None:
        return None
    lines = await _get_lines(db, entry.id)
    detail = JournalEntryDetail.model_validate(entry)
    detail.lines = [
        type("L", (), {**l.__dict__})
        for l in lines
    ]
    # Build detail with lines from ORM objects
    detail_dict = {
        **entry.__dict__,
        "lines": lines,
    }
    return detail


async def get_libro_giornale(
    db: AsyncSession,
    client_entity_id: uuid.UUID,
    fiscal_year_id: uuid.UUID,
    data_da: Optional[date] = None,
    data_a: Optional[date] = None,
    causale: Optional[str] = None,
) -> List[JournalEntry]:
    """Lista registrazioni posted ordinate per data_registrazione, numero_registrazione."""
    query = select(JournalEntry).where(
        JournalEntry.client_entity_id == client_entity_id,
        JournalEntry.fiscal_year_id == fiscal_year_id,
        JournalEntry.studio_id == STUDIO_UUID,
        JournalEntry.stato == "posted",
    )
    if data_da:
        query = query.where(JournalEntry.data_registrazione >= data_da)
    if data_a:
        query = query.where(JournalEntry.data_registrazione <= data_a)
    if causale:
        query = query.where(JournalEntry.causale == causale)

    query = query.order_by(JournalEntry.data_registrazione, JournalEntry.numero_registrazione)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_mastrino(
    db: AsyncSession,
    client_entity_id: uuid.UUID,
    account_id: uuid.UUID,
    fiscal_year_id: uuid.UUID,
) -> MastrinoOut:
    """Movimenti di un conto con saldo progressivo."""
    result = await db.execute(
        select(JournalLine, JournalEntry)
        .join(JournalEntry, JournalLine.journal_entry_id == JournalEntry.id)
        .where(
            JournalLine.account_id == account_id,
            JournalEntry.client_entity_id == client_entity_id,
            JournalEntry.fiscal_year_id == fiscal_year_id,
            JournalEntry.studio_id == STUDIO_UUID,
            JournalEntry.stato == "posted",
        )
        .order_by(JournalEntry.data_registrazione, JournalEntry.numero_registrazione)
    )
    rows = result.all()

    saldo_dare = Decimal("0")
    saldo_avere = Decimal("0")
    movimenti = []

    for line, entry in rows:
        d = _to_decimal(line.dare)
        a = _to_decimal(line.avere)
        saldo_dare += d
        saldo_avere += a
        movimenti.append(
            MastrinMovimento(
                journal_entry_id=entry.id,
                data_registrazione=entry.data_registrazione,
                numero_registrazione=entry.numero_registrazione,
                descrizione=entry.descrizione,
                dare=d,
                avere=a,
                saldo_progressivo=saldo_dare - saldo_avere,
            )
        )

    return MastrinoOut(
        account_id=account_id,
        movimenti=movimenti,
        tot_dare=saldo_dare,
        tot_avere=saldo_avere,
        saldo=saldo_dare - saldo_avere,
    )


async def get_bilancio_verifica(
    db: AsyncSession,
    client_entity_id: uuid.UUID,
    fiscal_year_id: uuid.UUID,
) -> List[BilancioVoce]:
    """Saldo dare/avere per ogni conto con movimenti nell'esercizio."""
    result = await db.execute(
        select(
            JournalLine.account_id,
            Account.codice,
            Account.nome,
            sqlfunc.sum(JournalLine.dare).label("tot_dare"),
            sqlfunc.sum(JournalLine.avere).label("tot_avere"),
        )
        .join(JournalEntry, JournalLine.journal_entry_id == JournalEntry.id)
        .join(Account, JournalLine.account_id == Account.id)
        .where(
            JournalEntry.client_entity_id == client_entity_id,
            JournalEntry.fiscal_year_id == fiscal_year_id,
            JournalEntry.studio_id == STUDIO_UUID,
            JournalEntry.stato == "posted",
        )
        .group_by(JournalLine.account_id, Account.codice, Account.nome)
        .order_by(Account.codice)
    )
    rows = result.all()

    return [
        BilancioVoce(
            account_id=r.account_id,
            codice=r.codice,
            nome=r.nome,
            tot_dare=_to_decimal(r.tot_dare),
            tot_avere=_to_decimal(r.tot_avere),
            saldo=_to_decimal(r.tot_dare) - _to_decimal(r.tot_avere),
        )
        for r in rows
    ]
