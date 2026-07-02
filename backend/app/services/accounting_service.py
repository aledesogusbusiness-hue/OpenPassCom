import uuid
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.accounting import AccountPlan, AccountType, Account
from app.schemas.accounting import AccountCreate

STUDIO_UUID = uuid.UUID(settings.STUDIO_ID)


async def get_account_plan_for_client(
    db: AsyncSession,
    client_entity_id: uuid.UUID,
) -> Optional[AccountPlan]:
    result = await db.execute(
        select(AccountPlan).where(
            AccountPlan.client_entity_id == client_entity_id,
            AccountPlan.studio_id == STUDIO_UUID,
            AccountPlan.is_default == True,
        )
    )
    return result.scalar_one_or_none()


async def list_accounts(
    db: AsyncSession,
    client_entity_id: uuid.UUID,
    account_type_id: Optional[uuid.UUID] = None,
) -> List[Account]:
    plan = await get_account_plan_for_client(db, client_entity_id)
    if not plan:
        return []

    query = select(Account).where(
        Account.account_plan_id == plan.id,
        Account.studio_id == STUDIO_UUID,
        Account.is_active == True,
    )
    if account_type_id:
        query = query.where(Account.account_type_id == account_type_id)

    query = query.order_by(Account.codice)
    result = await db.execute(query)
    return list(result.scalars().all())


async def create_account(
    db: AsyncSession,
    data: AccountCreate,
    created_by: uuid.UUID,
) -> Account:
    account = Account(
        id=uuid.uuid4(),
        studio_id=STUDIO_UUID,
        account_plan_id=data.account_plan_id,
        account_type_id=data.account_type_id,
        codice=data.codice,
        nome=data.nome,
        livello=data.livello,
        parent_id=data.parent_id,
        is_active=True,
    )
    db.add(account)
    await db.flush()
    return account


def build_account_tree(accounts: List[Account]) -> List[Account]:
    """Costruisce la gerarchia ad albero dei conti."""
    account_map = {a.id: a for a in accounts}
    # Inizializza children come lista vuota (transient attr)
    for a in accounts:
        a.__dict__.setdefault("children", [])

    roots = []
    for a in accounts:
        if a.parent_id and a.parent_id in account_map:
            parent = account_map[a.parent_id]
            parent.__dict__.setdefault("children", [])
            parent.__dict__["children"].append(a)
        else:
            roots.append(a)
    return roots


async def get_account_types(db: AsyncSession) -> List[AccountType]:
    result = await db.execute(select(AccountType).order_by(AccountType.tipo_codice))
    return list(result.scalars().all())
