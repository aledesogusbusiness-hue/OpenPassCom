"""
Router — Emissione fatture elettroniche verso SDI (Phase 9, infrastruttura lato nostro).
"""
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, verify_client_access
from app.models.auth import User
from app.schemas.tax import (
    FatturaPAExportCreate,
    FatturaPAExportLineOut,
    FatturaPAExportMarkEsitoIn,
    FatturaPAExportMarkInviataIn,
    FatturaPAExportOut,
)
from app.services import fattura_pa_export_service, parties_service

router = APIRouter(prefix="/api/v1", tags=["FatturaPA Emesse"], dependencies=[Depends(verify_client_access)])


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


async def _get_export_or_404(db: AsyncSession, client_id: uuid.UUID, year_id: uuid.UUID, export_id: uuid.UUID):
    exp = await fattura_pa_export_service.get_export(db, client_id, year_id, export_id)
    if not exp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fattura non trovata")
    return exp


async def _to_out(db: AsyncSession, export) -> FatturaPAExportOut:
    lines = await fattura_pa_export_service.get_lines(db, export.id)
    out = FatturaPAExportOut.model_validate(export)
    out.righe = [FatturaPAExportLineOut.model_validate(l) for l in lines]
    return out


@router.post(
    "/clients/{client_id}/fiscal-years/{year_id}/fatture-pa-export",
    response_model=FatturaPAExportOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_export(
    client_id: uuid.UUID,
    year_id: uuid.UUID,
    body: FatturaPAExportCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FatturaPAExportOut:
    await _get_client_or_404(db, client_id)
    await _get_fiscal_year_or_404(db, client_id, year_id)

    export = await fattura_pa_export_service.create_export(
        db, client_id, year_id, body, created_by=current_user.id
    )
    return await _to_out(db, export)


@router.get(
    "/clients/{client_id}/fiscal-years/{year_id}/fatture-pa-export",
    response_model=List[FatturaPAExportOut],
)
async def list_exports(
    client_id: uuid.UUID,
    year_id: uuid.UUID,
    stato: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[FatturaPAExportOut]:
    await _get_client_or_404(db, client_id)
    await _get_fiscal_year_or_404(db, client_id, year_id)

    exports = await fattura_pa_export_service.list_exports(db, client_id, year_id, stato=stato)
    return [await _to_out(db, e) for e in exports]


@router.get(
    "/clients/{client_id}/fiscal-years/{year_id}/fatture-pa-export/{export_id}",
    response_model=FatturaPAExportOut,
)
async def get_export(
    client_id: uuid.UUID,
    year_id: uuid.UUID,
    export_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FatturaPAExportOut:
    await _get_client_or_404(db, client_id)
    await _get_fiscal_year_or_404(db, client_id, year_id)
    export = await _get_export_or_404(db, client_id, year_id, export_id)
    return await _to_out(db, export)


@router.post(
    "/clients/{client_id}/fiscal-years/{year_id}/fatture-pa-export/{export_id}/generate-xml",
    response_model=FatturaPAExportOut,
)
async def generate_xml(
    client_id: uuid.UUID,
    year_id: uuid.UUID,
    export_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FatturaPAExportOut:
    client = await _get_client_or_404(db, client_id)
    await _get_fiscal_year_or_404(db, client_id, year_id)
    export = await _get_export_or_404(db, client_id, year_id, export_id)

    export = await fattura_pa_export_service.generate_xml(db, client, export)
    return await _to_out(db, export)


@router.get(
    "/clients/{client_id}/fiscal-years/{year_id}/fatture-pa-export/{export_id}/download",
)
async def download_xml(
    client_id: uuid.UUID,
    year_id: uuid.UUID,
    export_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    await _get_client_or_404(db, client_id)
    await _get_fiscal_year_or_404(db, client_id, year_id)
    export = await _get_export_or_404(db, client_id, year_id, export_id)

    if not export.xml_content:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="XML non ancora generato — usa /generate-xml prima di scaricare",
        )

    filename = f"IT{export.numero_fattura}_{export.tipo_documento}.xml"
    return Response(
        content=export.xml_content,
        media_type="application/xml",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post(
    "/clients/{client_id}/fiscal-years/{year_id}/fatture-pa-export/{export_id}/mark-inviata",
    response_model=FatturaPAExportOut,
)
async def mark_inviata(
    client_id: uuid.UUID,
    year_id: uuid.UUID,
    export_id: uuid.UUID,
    body: FatturaPAExportMarkInviataIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FatturaPAExportOut:
    await _get_client_or_404(db, client_id)
    await _get_fiscal_year_or_404(db, client_id, year_id)
    export = await _get_export_or_404(db, client_id, year_id, export_id)

    export = await fattura_pa_export_service.mark_inviata(db, export, body.identificativo_sdi)
    return await _to_out(db, export)


@router.post(
    "/clients/{client_id}/fiscal-years/{year_id}/fatture-pa-export/{export_id}/mark-esito",
    response_model=FatturaPAExportOut,
)
async def mark_esito(
    client_id: uuid.UUID,
    year_id: uuid.UUID,
    export_id: uuid.UUID,
    body: FatturaPAExportMarkEsitoIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FatturaPAExportOut:
    await _get_client_or_404(db, client_id)
    await _get_fiscal_year_or_404(db, client_id, year_id)
    export = await _get_export_or_404(db, client_id, year_id, export_id)

    export = await fattura_pa_export_service.mark_esito(db, export, body.esito, body.messaggio)
    return await _to_out(db, export)
