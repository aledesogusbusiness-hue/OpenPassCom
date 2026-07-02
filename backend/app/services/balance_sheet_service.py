"""
Balance Sheet Service — Stato patrimoniale, conto economico, chiusura esercizio.

Riusa get_bilancio_verifica da journal_service per i saldi per conto.
Per la classificazione SP/CE usa AccountType.tipo_codice.

Regole:
- SP-A: saldo = tot_dare - tot_avere (positivo = attivo)
- SP-P: saldo = tot_avere - tot_dare (positivo = passivo/PN)
- CE-R: saldo = tot_avere - tot_dare (positivo = ricavi)
- CE-C: saldo = tot_dare - tot_avere (positivo = costi)
- await db.flush(), MAI await db.commit()
"""
import uuid
from datetime import date
from decimal import Decimal
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.accounting import Account, AccountType
from app.models.balance import YearClosing
from app.models.parties import FiscalYear
from app.services.journal_service import get_bilancio_verifica

STUDIO_UUID = uuid.UUID(settings.STUDIO_ID)
_ZERO = Decimal("0")
_EPSILON = Decimal("0.01")


def _d(value) -> Decimal:
    if value is None:
        return _ZERO
    return Decimal(str(value))


async def _get_account_type_map(
    db: AsyncSession,
    account_ids: list[uuid.UUID],
) -> dict[uuid.UUID, str]:
    """Ritorna {account_id: tipo_codice} per i conti dati."""
    if not account_ids:
        return {}
    result = await db.execute(
        select(Account.id, AccountType.tipo_codice)
        .join(AccountType, Account.account_type_id == AccountType.id)
        .where(Account.id.in_(account_ids))
    )
    return {row[0]: row[1] for row in result.all()}


async def get_stato_patrimoniale(
    db: AsyncSession,
    client_entity_id: uuid.UUID,
    fiscal_year_id: uuid.UUID,
) -> dict:
    """
    Stato Patrimoniale riclassificato.
    Attivo  → conti SP-A (saldo dare > avere)
    Passivo → conti SP-P (saldo avere > dare)
    """
    voci = await get_bilancio_verifica(db, client_entity_id, fiscal_year_id)

    empty_section = {"voci": [], "totale": _ZERO}
    if not voci:
        return {
            "attivo": empty_section,
            "passivo": empty_section,
            "totale_attivo": _ZERO,
            "totale_passivo": _ZERO,
            "quadrato": True,
        }

    type_map = await _get_account_type_map(db, [v.account_id for v in voci])

    attivo_voci = []
    passivo_voci = []

    for v in voci:
        tipo = type_map.get(v.account_id)
        if tipo == "SP-A":
            saldo = _d(v.tot_dare) - _d(v.tot_avere)
            if saldo != _ZERO:
                attivo_voci.append({"codice": v.codice, "nome": v.nome, "saldo": saldo})
        elif tipo == "SP-P":
            saldo = _d(v.tot_avere) - _d(v.tot_dare)
            if saldo != _ZERO:
                passivo_voci.append({"codice": v.codice, "nome": v.nome, "saldo": saldo})

    totale_attivo = sum((r["saldo"] for r in attivo_voci), _ZERO)
    totale_passivo = sum((r["saldo"] for r in passivo_voci), _ZERO)

    return {
        "attivo": {"voci": attivo_voci, "totale": totale_attivo},
        "passivo": {"voci": passivo_voci, "totale": totale_passivo},
        "totale_attivo": totale_attivo,
        "totale_passivo": totale_passivo,
        "quadrato": abs(totale_attivo - totale_passivo) < _EPSILON,
    }


async def get_conto_economico(
    db: AsyncSession,
    client_entity_id: uuid.UUID,
    fiscal_year_id: uuid.UUID,
) -> dict:
    """
    Conto Economico riclassificato (schema scalare).
    CE-R (Ricavi): saldo = avere - dare
    CE-C (Costi):  saldo = dare - avere
    """
    voci = await get_bilancio_verifica(db, client_entity_id, fiscal_year_id)

    empty_section = {"voci": [], "totale": _ZERO}
    if not voci:
        return {
            "ricavi": empty_section,
            "costi": empty_section,
            "risultato_operativo": _ZERO,
            "utile_perdita": _ZERO,
        }

    type_map = await _get_account_type_map(db, [v.account_id for v in voci])

    ricavi_voci = []
    costi_voci = []

    for v in voci:
        tipo = type_map.get(v.account_id)
        if tipo == "CE-R":
            saldo = _d(v.tot_avere) - _d(v.tot_dare)
            if saldo != _ZERO:
                ricavi_voci.append({"codice": v.codice, "nome": v.nome, "saldo": saldo})
        elif tipo == "CE-C":
            saldo = _d(v.tot_dare) - _d(v.tot_avere)
            if saldo != _ZERO:
                costi_voci.append({"codice": v.codice, "nome": v.nome, "saldo": saldo})

    totale_ricavi = sum((r["saldo"] for r in ricavi_voci), _ZERO)
    totale_costi = sum((r["saldo"] for r in costi_voci), _ZERO)
    risultato = totale_ricavi - totale_costi

    return {
        "ricavi": {"voci": ricavi_voci, "totale": totale_ricavi},
        "costi": {"voci": costi_voci, "totale": totale_costi},
        "risultato_operativo": risultato,
        "utile_perdita": risultato,
    }


async def get_year_closing(
    db: AsyncSession,
    fiscal_year_id: uuid.UUID,
) -> Optional[YearClosing]:
    result = await db.execute(
        select(YearClosing).where(YearClosing.fiscal_year_id == fiscal_year_id)
    )
    return result.scalar_one_or_none()


async def close_fiscal_year(
    db: AsyncSession,
    client_entity_id: uuid.UUID,
    fiscal_year_id: uuid.UUID,
    created_by: uuid.UUID,
    note: Optional[str] = None,
) -> YearClosing:
    """
    Chiude l'esercizio fiscale:
    1. Verifica che l'esercizio non sia già chiuso (409 se chiuso)
    2. Calcola Stato Patrimoniale e Conto Economico
    3. Crea YearClosing con stato='chiuso'
    4. Imposta FiscalYear.stato='chiuso'
    """
    # Trova il FiscalYear
    fy_result = await db.execute(
        select(FiscalYear).where(
            FiscalYear.id == fiscal_year_id,
            FiscalYear.client_entity_id == client_entity_id,
            FiscalYear.studio_id == STUDIO_UUID,
        )
    )
    fy = fy_result.scalar_one_or_none()
    if fy is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Esercizio fiscale non trovato",
        )

    if fy.stato == "chiuso":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="L'esercizio fiscale è già chiuso",
        )

    # Calcola i dati di bilancio
    sp = await get_stato_patrimoniale(db, client_entity_id, fiscal_year_id)
    ce = await get_conto_economico(db, client_entity_id, fiscal_year_id)

    # Crea la chiusura
    closing = YearClosing(
        id=uuid.uuid4(),
        studio_id=STUDIO_UUID,
        client_entity_id=client_entity_id,
        fiscal_year_id=fiscal_year_id,
        stato="chiuso",
        data_chiusura=date.today(),
        note=note,
        totale_attivo=sp["totale_attivo"],
        totale_passivo=sp["totale_passivo"],
        totale_ricavi=ce["ricavi"]["totale"],
        totale_costi=ce["costi"]["totale"],
        utile_perdita=ce["utile_perdita"],
        created_by=created_by,
    )
    db.add(closing)

    # Chiudi l'esercizio fiscale
    fy.stato = "chiuso"
    await db.flush()
    await db.refresh(closing)

    return closing
