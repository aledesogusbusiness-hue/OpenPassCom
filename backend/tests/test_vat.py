"""
Test Phase 2 — Registro IVA.
Copre l'invariante 10bis (regime forfettario non può avere IVA).
"""
import uuid
from datetime import date
from decimal import Decimal

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.accounting import AccountPlan, Account
from app.models.journal import JournalEntry, SequenceCounter

pytestmark = pytest.mark.asyncio

STUDIO_ID = uuid.UUID(settings.STUDIO_ID)
AT_SP_A_ID = uuid.UUID("10000000-0000-0000-0000-000000000001")
AT_CE_R_ID = uuid.UUID("10000000-0000-0000-0000-000000000004")

# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture()
async def setup_ordinario(client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
    """Cliente ordinario + esercizio + conti + entry posted (per collegare vat_entries)."""
    resp = await client.post("/api/v1/clients", json={
        "ragione_sociale": "Azienda Ordinaria VAT S.r.l.",
        "fiscal_regime": "ordinario",
        "periodicita_iva": "mensile",
    }, headers=auth_headers)
    assert resp.status_code == 201, resp.text
    client_id = uuid.UUID(resp.json()["id"])

    fy_resp = await client.post(
        f"/api/v1/clients/{client_id}/fiscal-years",
        json={"anno": 2024, "data_inizio": "2024-01-01", "data_fine": "2024-12-31"},
        headers=auth_headers,
    )
    assert fy_resp.status_code == 201
    fy_id = uuid.UUID(fy_resp.json()["id"])

    # Piano conti + conti
    plan_id = uuid.uuid4()
    cassa_id = uuid.uuid4()
    ricavi_id = uuid.uuid4()
    db_session.add(AccountPlan(
        id=plan_id, studio_id=STUDIO_ID, client_entity_id=client_id,
        nome="Piano VAT Test", is_default=True,
    ))
    db_session.add(Account(
        id=cassa_id, studio_id=STUDIO_ID, account_plan_id=plan_id,
        account_type_id=AT_SP_A_ID, codice="1001", nome="Cassa", livello=1,
    ))
    db_session.add(Account(
        id=ricavi_id, studio_id=STUDIO_ID, account_plan_id=plan_id,
        account_type_id=AT_CE_R_ID, codice="4001", nome="Ricavi", livello=1,
    ))
    await db_session.flush()

    # Crea una JournalEntry posted (necessaria come FK per vat_entries)
    entry_id = uuid.uuid4()
    counter = SequenceCounter(
        id=uuid.uuid4(), studio_id=STUDIO_ID, client_entity_id=client_id,
        fiscal_year_id=fy_id, counter_name="journal", last_value=1,
    )
    db_session.add(counter)

    je = JournalEntry(
        id=entry_id, studio_id=STUDIO_ID, client_entity_id=client_id,
        fiscal_year_id=fy_id, numero_registrazione=1,
        data_registrazione=date(2024, 3, 15), descrizione="Vendita fattura",
        causale="FV", stato="posted",
    )
    db_session.add(je)
    await db_session.flush()

    return {
        "client_id": str(client_id),
        "fy_id": str(fy_id),
        "journal_entry_id": str(entry_id),
    }


@pytest_asyncio.fixture()
async def setup_forfettario(client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
    """Cliente forfettario + esercizio fiscale."""
    resp = await client.post("/api/v1/clients", json={
        "ragione_sociale": "Artigiano Forfettario",
        "fiscal_regime": "forfettario",
    }, headers=auth_headers)
    assert resp.status_code == 201, resp.text
    client_id = uuid.UUID(resp.json()["id"])

    fy_resp = await client.post(
        f"/api/v1/clients/{client_id}/fiscal-years",
        json={"anno": 2024, "data_inizio": "2024-01-01", "data_fine": "2024-12-31"},
        headers=auth_headers,
    )
    assert fy_resp.status_code == 201
    fy_id = uuid.UUID(fy_resp.json()["id"])

    # Serve una JournalEntry finta (anche in stato draft va bene per il test del blocco IVA)
    entry_id = uuid.uuid4()
    je = JournalEntry(
        id=entry_id, studio_id=STUDIO_ID, client_entity_id=client_id,
        fiscal_year_id=fy_id, numero_registrazione=1,
        data_registrazione=date(2024, 3, 15), descrizione="Nota spese",
        causale="IN", stato="draft",
    )
    db_session.add(je)
    await db_session.flush()

    return {
        "client_id": str(client_id),
        "fy_id": str(fy_id),
        "journal_entry_id": str(entry_id),
    }


# ── Test 1: crea vat entry per cliente ordinario ─────────────────────────────

async def test_create_vat_entry_ordinario(
    client: AsyncClient, auth_headers: dict, setup_ordinario: dict
) -> None:
    """Regime ordinario: creazione vat entry OK."""
    d = setup_ordinario
    payload = {
        "tipo": "vendite",
        "journal_entry_id": d["journal_entry_id"],
        "data_documento": "2024-03-15",
        "numero_documento": "001/2024",
        "controparte": "Cliente Bianchi",
        "imponibile": "1000.00",
        "aliquota": 22,
        "imposta": "220.00",
    }
    resp = await client.post(
        f"/api/v1/clients/{d['client_id']}/fiscal-years/{d['fy_id']}/vat/entries",
        json=payload,
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert Decimal(str(data["imponibile"])) == Decimal("1000.00")
    assert Decimal(str(data["imposta"])) == Decimal("220.00")
    assert data["aliquota"] == 22


# ── Test 2: invariante 10bis — forfettario non può avere IVA ─────────────────

async def test_forfettario_no_iva(
    client: AsyncClient, auth_headers: dict, setup_forfettario: dict
) -> None:
    """Invariante 10bis: regime forfettario → 422 se si tenta registrazione IVA."""
    d = setup_forfettario
    payload = {
        "tipo": "vendite",
        "journal_entry_id": d["journal_entry_id"],
        "data_documento": "2024-03-15",
        "imponibile": "500.00",
        "aliquota": 0,
        "imposta": "0.00",
    }
    resp = await client.post(
        f"/api/v1/clients/{d['client_id']}/fiscal-years/{d['fy_id']}/vat/entries",
        json=payload,
        headers=auth_headers,
    )
    assert resp.status_code == 422
    assert "forfettario" in resp.json()["detail"].lower()


# ── Test 3: liquidazione IVA mensile ─────────────────────────────────────────

async def test_vat_liquidazione_mensile(
    client: AsyncClient, auth_headers: dict, setup_ordinario: dict
) -> None:
    """Liquidazione IVA mensile: debito = iva_vendite − iva_acquisti."""
    d = setup_ordinario

    # Inserisci due vat_entry: 1 vendita e 1 acquisto
    vat_url = f"/api/v1/clients/{d['client_id']}/fiscal-years/{d['fy_id']}/vat/entries"

    await client.post(vat_url, json={
        "tipo": "vendite",
        "journal_entry_id": d["journal_entry_id"],
        "data_documento": "2024-03-10",
        "imponibile": "1000.00",
        "aliquota": 22,
        "imposta": "220.00",
    }, headers=auth_headers)

    await client.post(vat_url, json={
        "tipo": "acquisti",
        "journal_entry_id": d["journal_entry_id"],
        "data_documento": "2024-03-20",
        "imponibile": "500.00",
        "aliquota": 22,
        "imposta": "110.00",
    }, headers=auth_headers)

    resp = await client.get(
        f"/api/v1/clients/{d['client_id']}/fiscal-years/{d['fy_id']}/vat/liquidazione?periodo=2024-03",
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    liq = resp.json()
    assert Decimal(str(liq["iva_vendite"])) == Decimal("220.00")
    assert Decimal(str(liq["iva_acquisti"])) == Decimal("110.00")
    assert Decimal(str(liq["debito_credito"])) == Decimal("110.00")  # debito verso erario


# ── Test 4: lista vat entries ─────────────────────────────────────────────────

async def test_vat_entries_list(
    client: AsyncClient, auth_headers: dict, setup_ordinario: dict
) -> None:
    """Lista registro vendite: filtra correttamente per tipo."""
    d = setup_ordinario
    vat_url = f"/api/v1/clients/{d['client_id']}/fiscal-years/{d['fy_id']}/vat/entries"

    # 2 vendite
    for importo in ["100.00", "200.00"]:
        await client.post(vat_url, json={
            "tipo": "vendite",
            "journal_entry_id": d["journal_entry_id"],
            "data_documento": "2024-03-01",
            "imponibile": importo,
            "aliquota": 22,
            "imposta": str(round(float(importo) * 0.22, 2)),
        }, headers=auth_headers)

    # 1 acquisto
    await client.post(vat_url, json={
        "tipo": "acquisti",
        "journal_entry_id": d["journal_entry_id"],
        "data_documento": "2024-03-01",
        "imponibile": "50.00",
        "aliquota": 22,
        "imposta": "11.00",
    }, headers=auth_headers)

    # Verifica registro vendite
    resp_v = await client.get(
        f"/api/v1/clients/{d['client_id']}/fiscal-years/{d['fy_id']}/vat/vendite",
        headers=auth_headers,
    )
    assert resp_v.status_code == 200
    assert len(resp_v.json()) == 2

    # Verifica registro acquisti
    resp_a = await client.get(
        f"/api/v1/clients/{d['client_id']}/fiscal-years/{d['fy_id']}/vat/acquisti",
        headers=auth_headers,
    )
    assert resp_a.status_code == 200
    assert len(resp_a.json()) == 1
