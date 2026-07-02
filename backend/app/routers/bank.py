"""
Router — Riconciliazione bancaria (Phase 6).
"""
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.auth import User
from app.schemas.bank import (
    BankStatementCreate,
    BankStatementOut,
    BankTransactionCreate,
    BankTransactionOut,
    ReconcileIn,
    ReconciliationSummaryOut,
)
from app.services import bank_service, parties_service

router = APIRouter(prefix="/api/v1", tags=["Banca"])


async def _get_client_or_404(db: AsyncSession, client_id: uuid.UUID):
    client = await parties_service.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente non trovato")
    return client


async def _get_statement_or_404(
    db: AsyncSession,
    client_id: uuid.UUID,
    statement_id: uuid.UUID,
):
    stmts = await bank_service.list_bank_statements(db, client_id)
    for s in stmts:
        if s.id == statement_id:
            return s
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Estratto conto non trovato",
    )


async def _get_transaction_or_404(
    db: AsyncSession,
    statement_id: uuid.UUID,
    tx_id: uuid.UUID,
):
    tx = await bank_service.get_transaction(db, statement_id, tx_id)
    if not tx:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transazione non trovata",
        )
    return tx


@router.post(
    "/clients/{client_id}/bank-statements",
    response_model=BankStatementOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_bank_statement(
    client_id: uuid.UUID,
    body: BankStatementCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BankStatementOut:
    await _get_client_or_404(db, client_id)
    stmt = await bank_service.create_bank_statement(
        db, client_id, body, created_by=current_user.id
    )
    return BankStatementOut.model_validate(stmt)


@router.get(
    "/clients/{client_id}/bank-statements",
    response_model=List[BankStatementOut],
)
async def list_bank_statements(
    client_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[BankStatementOut]:
    await _get_client_or_404(db, client_id)
    stmts = await bank_service.list_bank_statements(db, client_id)
    return [BankStatementOut.model_validate(s) for s in stmts]


@router.post(
    "/clients/{client_id}/bank-statements/{statement_id}/transactions",
    response_model=List[BankTransactionOut],
    status_code=status.HTTP_201_CREATED,
)
async def import_transactions(
    client_id: uuid.UUID,
    statement_id: uuid.UUID,
    body: List[BankTransactionCreate],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[BankTransactionOut]:
    await _get_client_or_404(db, client_id)
    await _get_statement_or_404(db, client_id, statement_id)
    txs = await bank_service.import_transactions(db, statement_id, body)
    return [BankTransactionOut.model_validate(tx) for tx in txs]


@router.get(
    "/clients/{client_id}/bank-statements/{statement_id}/transactions",
    response_model=List[BankTransactionOut],
)
async def list_transactions(
    client_id: uuid.UUID,
    statement_id: uuid.UUID,
    stato: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[BankTransactionOut]:
    await _get_client_or_404(db, client_id)
    await _get_statement_or_404(db, client_id, statement_id)
    txs = await bank_service.list_transactions(db, statement_id, stato=stato)
    return [BankTransactionOut.model_validate(tx) for tx in txs]


@router.get(
    "/clients/{client_id}/bank-statements/{statement_id}/summary",
    response_model=ReconciliationSummaryOut,
)
async def get_summary(
    client_id: uuid.UUID,
    statement_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReconciliationSummaryOut:
    await _get_client_or_404(db, client_id)
    await _get_statement_or_404(db, client_id, statement_id)
    summary = await bank_service.get_reconciliation_summary(db, statement_id)
    return ReconciliationSummaryOut(**summary)


@router.post(
    "/clients/{client_id}/bank-statements/{statement_id}/transactions/{tx_id}/reconcile",
    response_model=BankTransactionOut,
)
async def reconcile_transaction(
    client_id: uuid.UUID,
    statement_id: uuid.UUID,
    tx_id: uuid.UUID,
    body: ReconcileIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BankTransactionOut:
    await _get_client_or_404(db, client_id)
    await _get_statement_or_404(db, client_id, statement_id)
    tx = await _get_transaction_or_404(db, statement_id, tx_id)
    tx = await bank_service.reconcile_transaction(
        db, tx,
        journal_entry_id=body.journal_entry_id,
        scheduled_payment_id=body.scheduled_payment_id,
        note=body.note,
    )
    return BankTransactionOut.model_validate(tx)


@router.post(
    "/clients/{client_id}/bank-statements/{statement_id}/transactions/{tx_id}/mark-irrilevante",
    response_model=BankTransactionOut,
)
async def mark_irrilevante(
    client_id: uuid.UUID,
    statement_id: uuid.UUID,
    tx_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BankTransactionOut:
    await _get_client_or_404(db, client_id)
    await _get_statement_or_404(db, client_id, statement_id)
    tx = await _get_transaction_or_404(db, statement_id, tx_id)
    tx = await bank_service.mark_irrilevante(db, tx)
    return BankTransactionOut.model_validate(tx)
