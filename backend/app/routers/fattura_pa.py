"""
Router — Import FatturaPA XML.
"""
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, verify_client_access
from app.models.auth import User
from app.schemas.journal import JournalEntryOut
from app.schemas.tax import (
    FatturaPAImportIn,
    FatturaPAImportOut,
    FatturaPAElaborateIn,
)
from app.services import fattura_pa_service, parties_service

router = APIRouter(prefix="/api/v1", tags=["FatturaPA"], dependencies=[Depends(verify_client_access)])


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


async def _get_import_or_404(db, client_id, year_id, import_id):
    imp = await fattura_pa_service.get_import(db, client_id, year_id, import_id)
    if not imp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import non trovato")
    return imp


@router.post(
    "/clients/{client_id}/fiscal-years/{year_id}/fatture-pa/import",
    response_model=FatturaPAImportOut,
    status_code=status.HTTP_201_CREATED,
)
async def import_fattura(
    client_id: uuid.UUID,
    year_id: uuid.UUID,
    body: FatturaPAImportIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FatturaPAImportOut:
    await _get_client_or_404(db, client_id)
    await _get_fiscal_year_or_404(db, client_id, year_id)

    imp = await fattura_pa_service.import_fattura(
        db,
        client_entity_id=client_id,
        fiscal_year_id=year_id,
        filename=body.filename,
        xml_content=body.xml_content,
        created_by=current_user.id,
    )
    return FatturaPAImportOut.model_validate(imp)


@router.get(
    "/clients/{client_id}/fiscal-years/{year_id}/fatture-pa",
    response_model=List[FatturaPAImportOut],
)
async def list_fatture_pa(
    client_id: uuid.UUID,
    year_id: uuid.UUID,
    stato: Optional[str] = Query(default=None, description="Filtro per stato"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[FatturaPAImportOut]:
    await _get_client_or_404(db, client_id)
    await _get_fiscal_year_or_404(db, client_id, year_id)

    imports = await fattura_pa_service.list_imports(db, client_id, year_id, stato=stato)
    return [FatturaPAImportOut.model_validate(i) for i in imports]


@router.get(
    "/clients/{client_id}/fiscal-years/{year_id}/fatture-pa/{import_id}",
    response_model=FatturaPAImportOut,
)
async def get_fattura_pa(
    client_id: uuid.UUID,
    year_id: uuid.UUID,
    import_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FatturaPAImportOut:
    await _get_client_or_404(db, client_id)
    await _get_fiscal_year_or_404(db, client_id, year_id)
    imp = await _get_import_or_404(db, client_id, year_id, import_id)
    return FatturaPAImportOut.model_validate(imp)


@router.post(
    "/clients/{client_id}/fiscal-years/{year_id}/fatture-pa/{import_id}/elaborate",
    status_code=status.HTTP_200_OK,
)
async def elaborate_fattura(
    client_id: uuid.UUID,
    year_id: uuid.UUID,
    import_id: uuid.UUID,
    body: FatturaPAElaborateIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    await _get_client_or_404(db, client_id)
    await _get_fiscal_year_or_404(db, client_id, year_id)
    imp = await _get_import_or_404(db, client_id, year_id, import_id)

    imp, entry = await fattura_pa_service.elaborate_fattura(
        db,
        imp=imp,
        account_id_fornitore=body.account_id_fornitore,
        account_id_iva=body.account_id_iva,
        account_id_debito=body.account_id_debito,
        created_by=current_user.id,
    )

    return {
        "import": FatturaPAImportOut.model_validate(imp).model_dump(mode="json"),
        "journal_entry": JournalEntryOut.model_validate(entry).model_dump(mode="json"),
    }
