"""
Router — Prima nota contabile (libro giornale, mastrino, bilancio di verifica).
"""
import uuid
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.auth import User
from app.schemas.journal import (
    JournalEntryCreate,
    JournalEntryOut,
    JournalEntryDetail,
    JournalLineOut,
    MastrinoOut,
    BilancioVoce,
)
from app.services import journal_service, parties_service

router = APIRouter(prefix="/api/v1", tags=["Prima nota"])


async def _get_client_or_404(db: AsyncSession, client_id: uuid.UUID):
    client = await parties_service.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente non trovato")
    return client


async def _get_fiscal_year_or_404(db: AsyncSession, client_id: uuid.UUID, year_id: uuid.UUID):
    fy = await parties_service.get_fiscal_year(db, client_id, year_id)
    if not fy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Esercizio fiscale non trovato")
    return fy


@router.post(
    "/clients/{client_id}/fiscal-years/{year_id}/journal-entries",
    response_model=JournalEntryOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_journal_entry(
    client_id: uuid.UUID,
    year_id: uuid.UUID,
    body: JournalEntryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JournalEntryOut:
    await _get_client_or_404(db, client_id)
    await _get_fiscal_year_or_404(db, client_id, year_id)

    entry = await journal_service.create_journal_entry(
        db, client_id, year_id, body, current_user.id
    )
    return JournalEntryOut.model_validate(entry)


@router.get(
    "/clients/{client_id}/fiscal-years/{year_id}/journal-entries",
    response_model=List[JournalEntryOut],
)
async def get_libro_giornale(
    client_id: uuid.UUID,
    year_id: uuid.UUID,
    data_da: Optional[date] = Query(None),
    data_a: Optional[date] = Query(None),
    causale: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[JournalEntryOut]:
    await _get_client_or_404(db, client_id)
    await _get_fiscal_year_or_404(db, client_id, year_id)

    entries = await journal_service.get_libro_giornale(
        db, client_id, year_id, data_da, data_a, causale
    )
    return [JournalEntryOut.model_validate(e) for e in entries]


@router.get(
    "/clients/{client_id}/fiscal-years/{year_id}/journal-entries/{entry_id}",
    response_model=JournalEntryDetail,
)
async def get_journal_entry_detail(
    client_id: uuid.UUID,
    year_id: uuid.UUID,
    entry_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JournalEntryDetail:
    from sqlalchemy import select
    from app.models.journal import JournalEntry, JournalLine

    await _get_client_or_404(db, client_id)
    await _get_fiscal_year_or_404(db, client_id, year_id)

    entry = await journal_service.get_journal_entry(db, client_id, year_id, entry_id)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registrazione non trovata")

    lines_result = await db.execute(
        select(JournalLine).where(JournalLine.journal_entry_id == entry.id)
    )
    lines = list(lines_result.scalars().all())

    detail = JournalEntryDetail.model_validate(entry)
    detail.lines = [JournalLineOut.model_validate(l) for l in lines]
    return detail


@router.post(
    "/clients/{client_id}/fiscal-years/{year_id}/journal-entries/{entry_id}/post",
    response_model=JournalEntryOut,
)
async def post_journal_entry(
    client_id: uuid.UUID,
    year_id: uuid.UUID,
    entry_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JournalEntryOut:
    await _get_client_or_404(db, client_id)
    await _get_fiscal_year_or_404(db, client_id, year_id)

    entry = await journal_service.get_journal_entry(db, client_id, year_id, entry_id)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registrazione non trovata")

    entry = await journal_service.post_journal_entry(db, entry)
    return JournalEntryOut.model_validate(entry)


@router.post(
    "/clients/{client_id}/fiscal-years/{year_id}/journal-entries/{entry_id}/reverse",
    response_model=JournalEntryOut,
    status_code=status.HTTP_201_CREATED,
)
async def reverse_journal_entry(
    client_id: uuid.UUID,
    year_id: uuid.UUID,
    entry_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JournalEntryOut:
    await _get_client_or_404(db, client_id)
    await _get_fiscal_year_or_404(db, client_id, year_id)

    entry = await journal_service.get_journal_entry(db, client_id, year_id, entry_id)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registrazione non trovata")

    new_entry = await journal_service.reverse_journal_entry(db, entry, current_user.id)
    return JournalEntryOut.model_validate(new_entry)


@router.get(
    "/clients/{client_id}/fiscal-years/{year_id}/mastrini/{account_id}",
    response_model=MastrinoOut,
)
async def get_mastrino(
    client_id: uuid.UUID,
    year_id: uuid.UUID,
    account_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MastrinoOut:
    await _get_client_or_404(db, client_id)
    await _get_fiscal_year_or_404(db, client_id, year_id)

    return await journal_service.get_mastrino(db, client_id, account_id, year_id)


@router.get(
    "/clients/{client_id}/fiscal-years/{year_id}/bilancio-verifica",
    response_model=List[BilancioVoce],
)
async def get_bilancio_verifica(
    client_id: uuid.UUID,
    year_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[BilancioVoce]:
    await _get_client_or_404(db, client_id)
    await _get_fiscal_year_or_404(db, client_id, year_id)

    return await journal_service.get_bilancio_verifica(db, client_id, year_id)
