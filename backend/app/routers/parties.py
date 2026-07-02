import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.log import log_action
from app.database import get_db
from app.dependencies import get_current_user
from app.models.auth import User
from app.schemas.parties import (
    ClientEntityCreate,
    ClientEntityOut,
    ClientEntityUpdate,
    FiscalYearCreate,
    FiscalYearOut,
)
from app.services import parties_service

router = APIRouter(prefix="/api/v1", tags=["Aziende clienti"])


# ── Clienti ──────────────────────────────────────────────────────────────────

@router.get("/clients", response_model=List[ClientEntityOut])
async def list_clients(
    include_inactive: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[ClientEntityOut]:
    clients = await parties_service.list_clients(db, include_inactive=include_inactive)
    return [ClientEntityOut.model_validate(c) for c in clients]


@router.post("/clients", response_model=ClientEntityOut, status_code=status.HTTP_201_CREATED)
async def create_client(
    body: ClientEntityCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ClientEntityOut:
    client = await parties_service.create_client(db, body, current_user.id)

    await log_action(
        db=db,
        user_id=current_user.id,
        action="create_client",
        entity_type="ClientEntity",
        entity_id=str(client.id),
        payload={"ragione_sociale": client.ragione_sociale},
        ip=request.client.host if request.client else None,
    )

    return ClientEntityOut.model_validate(client)


@router.get("/clients/{client_id}", response_model=ClientEntityOut)
async def get_client(
    client_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ClientEntityOut:
    client = await parties_service.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente non trovato")
    return ClientEntityOut.model_validate(client)


@router.put("/clients/{client_id}", response_model=ClientEntityOut)
async def update_client(
    client_id: uuid.UUID,
    body: ClientEntityUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ClientEntityOut:
    client = await parties_service.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente non trovato")

    client = await parties_service.update_client(db, client, body, current_user.id)

    await log_action(
        db=db,
        user_id=current_user.id,
        action="update_client",
        entity_type="ClientEntity",
        entity_id=str(client.id),
        payload=body.model_dump(exclude_unset=True),
        ip=request.client.host if request.client else None,
    )

    return ClientEntityOut.model_validate(client)


@router.delete("/clients/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(
    client_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    client = await parties_service.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente non trovato")

    await parties_service.deactivate_client(db, client, current_user.id)

    await log_action(
        db=db,
        user_id=current_user.id,
        action="deactivate_client",
        entity_type="ClientEntity",
        entity_id=str(client.id),
        ip=request.client.host if request.client else None,
    )


# ── Esercizi fiscali ──────────────────────────────────────────────────────────

@router.get("/clients/{client_id}/fiscal-years", response_model=List[FiscalYearOut])
async def list_fiscal_years(
    client_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[FiscalYearOut]:
    client = await parties_service.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente non trovato")

    fiscal_years = await parties_service.list_fiscal_years(db, client_id)
    return [FiscalYearOut.model_validate(fy) for fy in fiscal_years]


@router.post(
    "/clients/{client_id}/fiscal-years",
    response_model=FiscalYearOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_fiscal_year(
    client_id: uuid.UUID,
    body: FiscalYearCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FiscalYearOut:
    client = await parties_service.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente non trovato")

    existing = await parties_service.get_fiscal_year_by_anno(db, client_id, body.anno)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Esercizio fiscale {body.anno} già esistente per questo cliente",
        )

    fy = await parties_service.create_fiscal_year(db, client_id, body, current_user.id)

    await log_action(
        db=db,
        user_id=current_user.id,
        action="create_fiscal_year",
        entity_type="FiscalYear",
        entity_id=str(fy.id),
        payload={"anno": fy.anno, "client_entity_id": str(client_id)},
        ip=request.client.host if request.client else None,
    )

    return FiscalYearOut.model_validate(fy)


@router.post(
    "/clients/{client_id}/fiscal-years/{year_id}/close",
    response_model=FiscalYearOut,
)
async def close_fiscal_year(
    client_id: uuid.UUID,
    year_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FiscalYearOut:
    client = await parties_service.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente non trovato")

    fy = await parties_service.get_fiscal_year(db, client_id, year_id)
    if not fy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Esercizio fiscale non trovato")

    if fy.stato == "chiuso":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="L'esercizio fiscale è già chiuso",
        )

    fy = await parties_service.close_fiscal_year(db, fy)

    await log_action(
        db=db,
        user_id=current_user.id,
        action="close_fiscal_year",
        entity_type="FiscalYear",
        entity_id=str(fy.id),
        payload={"anno": fy.anno, "client_entity_id": str(client_id)},
        ip=request.client.host if request.client else None,
    )

    return FiscalYearOut.model_validate(fy)
