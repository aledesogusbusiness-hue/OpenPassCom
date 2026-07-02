import uuid
from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.parties import ClientEntity, FiscalYear
from app.schemas.parties import ClientEntityCreate, ClientEntityUpdate, FiscalYearCreate


STUDIO_UUID = uuid.UUID(settings.STUDIO_ID)


async def list_clients(db: AsyncSession, include_inactive: bool = False) -> List[ClientEntity]:
    query = select(ClientEntity).where(ClientEntity.studio_id == STUDIO_UUID)
    if not include_inactive:
        query = query.where(ClientEntity.is_active == True)
    query = query.order_by(ClientEntity.ragione_sociale)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_client(db: AsyncSession, client_id: uuid.UUID) -> Optional[ClientEntity]:
    result = await db.execute(
        select(ClientEntity).where(
            ClientEntity.id == client_id,
            ClientEntity.studio_id == STUDIO_UUID,
        )
    )
    return result.scalar_one_or_none()


async def create_client(
    db: AsyncSession,
    data: ClientEntityCreate,
    created_by: uuid.UUID,
) -> ClientEntity:
    client = ClientEntity(
        id=uuid.uuid4(),
        studio_id=STUDIO_UUID,
        ragione_sociale=data.ragione_sociale,
        codice_fiscale=data.codice_fiscale,
        partita_iva=data.partita_iva,
        fiscal_regime=data.fiscal_regime,
        periodicita_iva=data.periodicita_iva,
        note=data.note,
        is_active=True,
        created_by=created_by,
        updated_by=created_by,
    )
    db.add(client)
    await db.flush()
    return client


async def update_client(
    db: AsyncSession,
    client: ClientEntity,
    data: ClientEntityUpdate,
    updated_by: uuid.UUID,
) -> ClientEntity:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(client, field, value)
    client.updated_by = updated_by
    await db.flush()
    return client


async def deactivate_client(
    db: AsyncSession,
    client: ClientEntity,
    updated_by: uuid.UUID,
) -> ClientEntity:
    client.is_active = False
    client.updated_by = updated_by
    await db.flush()
    return client


async def list_fiscal_years(
    db: AsyncSession,
    client_entity_id: uuid.UUID,
) -> List[FiscalYear]:
    result = await db.execute(
        select(FiscalYear)
        .where(
            FiscalYear.client_entity_id == client_entity_id,
            FiscalYear.studio_id == STUDIO_UUID,
        )
        .order_by(FiscalYear.anno.desc())
    )
    return list(result.scalars().all())


async def get_fiscal_year(
    db: AsyncSession,
    client_entity_id: uuid.UUID,
    year_id: uuid.UUID,
) -> Optional[FiscalYear]:
    result = await db.execute(
        select(FiscalYear).where(
            FiscalYear.id == year_id,
            FiscalYear.client_entity_id == client_entity_id,
            FiscalYear.studio_id == STUDIO_UUID,
        )
    )
    return result.scalar_one_or_none()


async def get_fiscal_year_by_anno(
    db: AsyncSession,
    client_entity_id: uuid.UUID,
    anno: int,
) -> Optional[FiscalYear]:
    result = await db.execute(
        select(FiscalYear).where(
            FiscalYear.client_entity_id == client_entity_id,
            FiscalYear.anno == anno,
            FiscalYear.studio_id == STUDIO_UUID,
        )
    )
    return result.scalar_one_or_none()


async def create_fiscal_year(
    db: AsyncSession,
    client_entity_id: uuid.UUID,
    data: FiscalYearCreate,
    created_by: uuid.UUID,
) -> FiscalYear:
    fy = FiscalYear(
        id=uuid.uuid4(),
        studio_id=STUDIO_UUID,
        client_entity_id=client_entity_id,
        anno=data.anno,
        data_inizio=data.data_inizio,
        data_fine=data.data_fine,
        stato="aperto",
        created_by=created_by,
    )
    db.add(fy)
    await db.flush()
    return fy


async def close_fiscal_year(
    db: AsyncSession,
    fiscal_year: FiscalYear,
) -> FiscalYear:
    fiscal_year.stato = "chiuso"
    await db.flush()
    return fiscal_year
