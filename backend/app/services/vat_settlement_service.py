"""
VAT Settlement Service — Liquidazione IVA periodica.

Calcola iva_vendite, iva_acquisti dal registro IVA, determina
debito_versare o credito_periodo, crea/aggiorna VatSettlement.
"""
import uuid
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.tax import VatSettlement
from app.services.vat_service import get_vat_liquidazione

STUDIO_UUID = uuid.UUID(settings.STUDIO_ID)

TWO_PLACES = Decimal("0.01")

# Mappa codici tributo IVA mensile (mese → codice)
_CODICI_MENSILI = {
    1: ("6001", "IVA mensile gennaio"),
    2: ("6002", "IVA mensile febbraio"),
    3: ("6003", "IVA mensile marzo"),
    4: ("6004", "IVA mensile aprile"),
    5: ("6005", "IVA mensile maggio"),
    6: ("6006", "IVA mensile giugno"),
    7: ("6007", "IVA mensile luglio"),
    8: ("6008", "IVA mensile agosto"),
    9: ("6009", "IVA mensile settembre"),
    10: ("6010", "IVA mensile ottobre"),
    11: ("6011", "IVA mensile novembre"),
    12: ("6012", "IVA mensile dicembre"),
}

# Mappa codici tributo IVA trimestrale (trimestre → codice)
_CODICI_TRIMESTRALI = {
    1: ("6031", "IVA trimestrale 1° trimestre"),
    2: ("6032", "IVA trimestrale 2° trimestre"),
    3: ("6033", "IVA trimestrale 3° trimestre"),
    4: ("6099", "IVA trimestrale 4° trimestre / saldo annuale"),
}


def _parse_periodo(periodo: str):
    """
    Restituisce (tipo_periodo, chiave_codice) dove chiave_codice è mese (int)
    per mensile o trimestre (int) per trimestrale.
    """
    if "Q" in periodo:
        _, q_str = periodo.split("-Q")
        return "trimestrale", int(q_str)
    else:
        _, m_str = periodo.split("-")
        return "mensile", int(m_str)


def _to_decimal(value) -> Decimal:
    if value is None:
        return Decimal("0")
    return Decimal(str(value))


async def compute_settlement(
    db: AsyncSession,
    client_entity_id: uuid.UUID,
    fiscal_year_id: uuid.UUID,
    periodo: str,
    credito_precedente: Decimal = Decimal("0"),
) -> VatSettlement:
    """
    Calcola la liquidazione IVA per il periodo.
    Crea o aggiorna VatSettlement in stato 'bozza'.
    """
    tipo_periodo, _ = _parse_periodo(periodo)

    # Recupera totali IVA dal registro
    liquidazione = await get_vat_liquidazione(db, client_entity_id, fiscal_year_id, periodo)
    iva_vendite = _to_decimal(liquidazione.iva_vendite).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
    iva_acquisti = _to_decimal(liquidazione.iva_acquisti).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
    credito_precedente = credito_precedente.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

    # Calcola debito/credito del periodo
    saldo = iva_vendite - iva_acquisti - credito_precedente
    if saldo > Decimal("0"):
        debito_versare = saldo.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        credito_periodo = Decimal("0")
    else:
        debito_versare = Decimal("0")
        credito_periodo = (-saldo).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

    # Cerca esistente (unico per studio/cliente/esercizio/periodo)
    result = await db.execute(
        select(VatSettlement).where(
            VatSettlement.studio_id == STUDIO_UUID,
            VatSettlement.client_entity_id == client_entity_id,
            VatSettlement.fiscal_year_id == fiscal_year_id,
            VatSettlement.periodo == periodo,
        )
    )
    settlement = result.scalar_one_or_none()

    if settlement is None:
        settlement = VatSettlement(
            id=uuid.uuid4(),
            studio_id=STUDIO_UUID,
            client_entity_id=client_entity_id,
            fiscal_year_id=fiscal_year_id,
            periodo=periodo,
            tipo_periodo=tipo_periodo,
            iva_vendite=iva_vendite,
            iva_acquisti=iva_acquisti,
            credito_precedente=credito_precedente,
            debito_versare=debito_versare,
            credito_periodo=credito_periodo,
            stato="bozza",
        )
        db.add(settlement)
    else:
        # Aggiorna solo se ancora in bozza
        if settlement.stato != "bozza":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"La liquidazione per il periodo {periodo} è già in stato '{settlement.stato}' e non può essere ricalcolata",
            )
        settlement.tipo_periodo = tipo_periodo
        settlement.iva_vendite = iva_vendite
        settlement.iva_acquisti = iva_acquisti
        settlement.credito_precedente = credito_precedente
        settlement.debito_versare = debito_versare
        settlement.credito_periodo = credito_periodo

    await db.flush()
    await db.refresh(settlement)
    return settlement


async def confirm_settlement(db: AsyncSession, settlement: VatSettlement) -> VatSettlement:
    """Porta la liquidazione da 'bozza' a 'confermata'."""
    if settlement.stato != "bozza":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Solo le liquidazioni in stato 'bozza' possono essere confermate (stato: {settlement.stato})",
        )
    settlement.stato = "confermata"
    await db.flush()
    await db.refresh(settlement)
    return settlement


async def mark_versata(
    db: AsyncSession,
    settlement: VatSettlement,
    data_versamento: date,
    f24_riferimento: Optional[str] = None,
) -> VatSettlement:
    """Porta la liquidazione a 'versata', registra data e riferimento F24."""
    if settlement.stato not in ("bozza", "confermata"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"La liquidazione non può essere marcata versata (stato: {settlement.stato})",
        )
    settlement.stato = "versata"
    settlement.data_versamento = data_versamento
    if f24_riferimento is not None:
        settlement.f24_riferimento = f24_riferimento
    await db.flush()
    await db.refresh(settlement)
    return settlement


async def get_settlements(
    db: AsyncSession,
    client_entity_id: uuid.UUID,
    fiscal_year_id: uuid.UUID,
) -> List[VatSettlement]:
    """Lista liquidazioni per cliente/esercizio."""
    result = await db.execute(
        select(VatSettlement).where(
            VatSettlement.studio_id == STUDIO_UUID,
            VatSettlement.client_entity_id == client_entity_id,
            VatSettlement.fiscal_year_id == fiscal_year_id,
        ).order_by(VatSettlement.periodo)
    )
    return list(result.scalars().all())


async def get_settlement(
    db: AsyncSession,
    client_entity_id: uuid.UUID,
    fiscal_year_id: uuid.UUID,
    settlement_id: uuid.UUID,
) -> Optional[VatSettlement]:
    result = await db.execute(
        select(VatSettlement).where(
            VatSettlement.id == settlement_id,
            VatSettlement.studio_id == STUDIO_UUID,
            VatSettlement.client_entity_id == client_entity_id,
            VatSettlement.fiscal_year_id == fiscal_year_id,
        )
    )
    return result.scalar_one_or_none()


async def get_f24_prospetto(
    db: AsyncSession,
    client_entity_id: uuid.UUID,
    fiscal_year_id: uuid.UUID,
    periodo: str,
) -> dict:
    """
    Genera prospetto F24 per il periodo.

    Codici tributo IVA mensili:  6001–6012
    Codici tributo IVA trimestrali: 6031 (Q1), 6032 (Q2), 6033 (Q3), 6099 (Q4/saldo)
    """
    result = await db.execute(
        select(VatSettlement).where(
            VatSettlement.studio_id == STUDIO_UUID,
            VatSettlement.client_entity_id == client_entity_id,
            VatSettlement.fiscal_year_id == fiscal_year_id,
            VatSettlement.periodo == periodo,
        )
    )
    settlement = result.scalar_one_or_none()
    if settlement is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Nessuna liquidazione trovata per il periodo {periodo}",
        )

    tipo_periodo, chiave = _parse_periodo(periodo)

    if tipo_periodo == "mensile":
        codice, descrizione = _CODICI_MENSILI[chiave]
    else:
        codice, descrizione = _CODICI_TRIMESTRALI[chiave]

    debito = _to_decimal(settlement.debito_versare)
    sezione_erario = []
    if debito > Decimal("0"):
        sezione_erario.append({
            "codice_tributo": codice,
            "descrizione": descrizione,
            "importo": debito,
        })

    return {
        "periodo": periodo,
        "tipo_periodo": tipo_periodo,
        "sezione_erario": sezione_erario,
        "sezione_contributi": [],
        "totale_saldo": debito,
    }
