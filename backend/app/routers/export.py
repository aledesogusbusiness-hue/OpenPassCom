"""
Router — Export PDF/Excel bilancio e libro giornale (Phase 7).
"""
import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.auth import User
from app.services import balance_sheet_service, export_service, parties_service

router = APIRouter(prefix="/api/v1", tags=["Export"])

_MEDIA_TYPES = {
    "pdf": "application/pdf",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


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


@router.get("/clients/{client_id}/fiscal-years/{year_id}/export/bilancio")
async def export_bilancio(
    client_id: uuid.UUID,
    year_id: uuid.UUID,
    format: Literal["pdf", "xlsx"] = Query(default="pdf"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    client = await _get_client_or_404(db, client_id)
    fy = await _get_fiscal_year_or_404(db, client_id, year_id)

    sp = await balance_sheet_service.get_stato_patrimoniale(db, client_id, year_id)
    ce = await balance_sheet_service.get_conto_economico(db, client_id, year_id)

    if format == "pdf":
        content = export_service.generate_bilancio_pdf(client.ragione_sociale, fy.anno, sp, ce)
        filename = f"bilancio_{fy.anno}.pdf"
    else:
        content = export_service.generate_bilancio_excel(client.ragione_sociale, fy.anno, sp, ce)
        filename = f"bilancio_{fy.anno}.xlsx"

    return Response(
        content=content,
        media_type=_MEDIA_TYPES[format],
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/clients/{client_id}/fiscal-years/{year_id}/export/libro-giornale")
async def export_libro_giornale(
    client_id: uuid.UUID,
    year_id: uuid.UUID,
    format: Literal["pdf", "xlsx"] = Query(default="pdf"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    client = await _get_client_or_404(db, client_id)
    fy = await _get_fiscal_year_or_404(db, client_id, year_id)

    entries = await export_service.get_libro_giornale_dettaglio(db, client_id, year_id)

    if format == "pdf":
        content = export_service.generate_giornale_pdf(client.ragione_sociale, fy.anno, entries)
        filename = f"libro_giornale_{fy.anno}.pdf"
    else:
        content = export_service.generate_giornale_excel(client.ragione_sociale, fy.anno, entries)
        filename = f"libro_giornale_{fy.anno}.xlsx"

    return Response(
        content=content,
        media_type=_MEDIA_TYPES[format],
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
