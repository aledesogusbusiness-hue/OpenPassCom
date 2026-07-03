import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, verify_client_access
from app.models.auth import User
from app.schemas.accounting import AccountCreate, AccountOut, AccountPlanOut, AccountTypeOut
from app.services import accounting_service, parties_service

router = APIRouter(prefix="/api/v1", tags=["Piano dei conti"], dependencies=[Depends(verify_client_access)])


@router.get("/clients/{client_id}/account-plan", response_model=AccountPlanOut)
async def get_account_plan(
    client_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AccountPlanOut:
    client = await parties_service.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente non trovato")

    plan = await accounting_service.get_account_plan_for_client(db, client_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Piano dei conti non trovato per questo cliente",
        )

    return AccountPlanOut.model_validate(plan)


@router.get("/clients/{client_id}/accounts", response_model=List[AccountOut])
async def list_accounts(
    client_id: uuid.UUID,
    account_type_id: Optional[uuid.UUID] = Query(None),
    flat: bool = Query(False, description="Se True restituisce lista piatta, altrimenti albero"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[AccountOut]:
    client = await parties_service.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente non trovato")

    accounts = await accounting_service.list_accounts(db, client_id, account_type_id)

    if flat:
        return [AccountOut.model_validate(a) for a in accounts]

    tree = accounting_service.build_account_tree(accounts)
    return [AccountOut.model_validate(a) for a in tree]


@router.post(
    "/clients/{client_id}/accounts",
    response_model=AccountOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_account(
    client_id: uuid.UUID,
    body: AccountCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AccountOut:
    client = await parties_service.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente non trovato")

    account = await accounting_service.create_account(db, body, current_user.id)
    return AccountOut.model_validate(account)


@router.get("/account-types", response_model=List[AccountTypeOut])
async def list_account_types(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[AccountTypeOut]:
    types = await accounting_service.get_account_types(db)
    return [AccountTypeOut.model_validate(t) for t in types]
