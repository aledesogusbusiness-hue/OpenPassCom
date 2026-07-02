"""
Test Phase 3 — Liquidazione IVA periodica.
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
from app.models.journal import JournalEntry, SequenceCounter, VatRegister, VatEntry

pytestmark = pytest.mark.asyncio

STUDIO_ID = uuid.UUID(settings.STUDIO_ID)
AT_SP_A_ID = uuid.UUID("10000000-0000-0000-0000-000000000001")
AT_CE_R_ID = uuid.UUID("10000000-0000-0000-0000-000000000004")


# ── Fixture base ──────────────────────────────────────────────────────────────

@pytest_asyncio.fixture()
async def setup_base(client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
    """Cliente ordinario + esercizio + registri IVA + entry."""
    resp = await client.post("/api/v1/clients", json={
        "ragione_sociale": "Azienda Test Settlement SRL",
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

    # Crea registri IVA e voci per il periodo 2024-01 (gennaio)
    reg_vendite = VatRegister(
        id=uuid.uuid4(), studio_id=STUDIO_ID, client_entity_id=client_id,
        fiscal_year_id=fy_id, tipo="vendite",
    )
    reg_acquisti = VatRegister(
        id=uuid.uuid4(), studio_id=STUDIO_ID, client_entity_id=client_id,
        fiscal_year_id=fy_id, tipo="acquisti",
    )
    db_session.add(reg_vendite)
    db_session.add(reg_acquisti)
    await db_session.flush()

    # JournalEntry fittizia come riferimento
    je = JournalEntry(
        id=uuid.uuid4(), studio_id=STUDIO_ID, client_entity_id=client_id,
        fiscal_year_id=fy_id, numero_registrazione=1,
        data_registrazione=date(2024, 1, 15), descrizione="Vendita gennaio",
        causale="FV", stato="posted",
    )
    db_session.add(je)
    await db_session.flush()

    # IVA vendite gennaio: 500.00
    db_session.add(VatEntry(
        id=uuid.uuid4(), studio_id=STUDIO_ID, vat_register_id=reg_vendite.id,
        journal_entry_id=je.id, data_documento=date(2024, 1, 15),
        imponibile=Decimal("2272.73"), aliquota=22, imposta=Decimal("500.00"),
    ))
    # IVA acquisti gennaio: 200.00
    db_session.add(VatEntry(
        id=uuid.uuid4(), studio_id=STUDIO_ID, vat_register_id=reg_acquisti.id,
        journal_entry_id=je.id, data_documento=date(2024, 1, 20),
        imponibile=Decimal("909.09"), aliquota=22, imposta=Decimal("200.00"),
    ))
    await db_session.flush()

    return {
        "client_id": str(client_id),
        "fy_id": str(fy_id),
    }


# ── Test 1: liquidazione con debito da versare ────────────────────────────────

async def test_compute_settlement_debito(
    client: AsyncClient, auth_headers: dict, setup_base: dict
) -> None:
    """Iva vendite > acquisti → debito_versare > 0, credito_periodo = 0."""
    d = setup_base
    resp = await client.post(
        f"/api/v1/clients/{d['client_id']}/fiscal-years/{d['fy_id']}/vat-settlements/compute",
        json={"periodo": "2024-01", "credito_precedente": "0"},
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["periodo"] == "2024-01"
    assert body["tipo_periodo"] == "mensile"
    assert Decimal(str(body["iva_vendite"])) == Decimal("500.00")
    assert Decimal(str(body["iva_acquisti"])) == Decimal("200.00")
    assert Decimal(str(body["debito_versare"])) == Decimal("300.00")
    assert Decimal(str(body["credito_periodo"])) == Decimal("0.00")
    assert body["stato"] == "bozza"


# ── Test 2: liquidazione con credito (acquisti > vendite) ─────────────────────

@pytest_asyncio.fixture()
async def setup_credito(client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
    """Cliente con acquisti > vendite nello stesso periodo."""
    resp = await client.post("/api/v1/clients", json={
        "ragione_sociale": "Azienda Credito IVA SRL",
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
    fy_id = uuid.UUID(fy_resp.json()["id"])

    reg_v = VatRegister(id=uuid.uuid4(), studio_id=STUDIO_ID, client_entity_id=client_id,
                        fiscal_year_id=fy_id, tipo="vendite")
    reg_a = VatRegister(id=uuid.uuid4(), studio_id=STUDIO_ID, client_entity_id=client_id,
                        fiscal_year_id=fy_id, tipo="acquisti")
    db_session.add(reg_v)
    db_session.add(reg_a)

    je = JournalEntry(id=uuid.uuid4(), studio_id=STUDIO_ID, client_entity_id=client_id,
                      fiscal_year_id=fy_id, numero_registrazione=1,
                      data_registrazione=date(2024, 2, 10), descrizione="Acquisto febbraio",
                      causale="FA", stato="posted")
    db_session.add(je)
    await db_session.flush()

    # IVA vendite: 100, acquisti: 400 → credito: 300
    db_session.add(VatEntry(id=uuid.uuid4(), studio_id=STUDIO_ID, vat_register_id=reg_v.id,
                             journal_entry_id=je.id, data_documento=date(2024, 2, 5),
                             imponibile=Decimal("454.55"), aliquota=22, imposta=Decimal("100.00")))
    db_session.add(VatEntry(id=uuid.uuid4(), studio_id=STUDIO_ID, vat_register_id=reg_a.id,
                             journal_entry_id=je.id, data_documento=date(2024, 2, 10),
                             imponibile=Decimal("1818.18"), aliquota=22, imposta=Decimal("400.00")))
    await db_session.flush()

    return {"client_id": str(client_id), "fy_id": str(fy_id)}


async def test_compute_settlement_credito(
    client: AsyncClient, auth_headers: dict, setup_credito: dict
) -> None:
    """Acquisti > vendite → credito_periodo > 0, debito_versare = 0."""
    d = setup_credito
    resp = await client.post(
        f"/api/v1/clients/{d['client_id']}/fiscal-years/{d['fy_id']}/vat-settlements/compute",
        json={"periodo": "2024-02", "credito_precedente": "0"},
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert Decimal(str(body["iva_vendite"])) == Decimal("100.00")
    assert Decimal(str(body["iva_acquisti"])) == Decimal("400.00")
    assert Decimal(str(body["debito_versare"])) == Decimal("0.00")
    assert Decimal(str(body["credito_periodo"])) == Decimal("300.00")


# ── Test 3: credito precedente riduce il debito ────────────────────────────────

async def test_credito_precedente(
    client: AsyncClient, auth_headers: dict, setup_base: dict
) -> None:
    """Un credito precedente di 100 riduce il debito da 300 a 200."""
    d = setup_base
    resp = await client.post(
        f"/api/v1/clients/{d['client_id']}/fiscal-years/{d['fy_id']}/vat-settlements/compute",
        json={"periodo": "2024-01", "credito_precedente": "100.00"},
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    # debito = 500 - 200 - 100 = 200
    assert Decimal(str(body["debito_versare"])) == Decimal("200.00")
    assert Decimal(str(body["credito_periodo"])) == Decimal("0.00")
    assert Decimal(str(body["credito_precedente"])) == Decimal("100.00")


# ── Test 4: bozza → confermata ────────────────────────────────────────────────

async def test_confirm_settlement(
    client: AsyncClient, auth_headers: dict, setup_base: dict
) -> None:
    """Liquidazione bozza può essere confermata."""
    d = setup_base
    # Calcola prima
    resp_compute = await client.post(
        f"/api/v1/clients/{d['client_id']}/fiscal-years/{d['fy_id']}/vat-settlements/compute",
        json={"periodo": "2024-01", "credito_precedente": "0"},
        headers=auth_headers,
    )
    assert resp_compute.status_code == 200
    settlement_id = resp_compute.json()["id"]

    # Conferma
    resp = await client.post(
        f"/api/v1/clients/{d['client_id']}/fiscal-years/{d['fy_id']}/vat-settlements/{settlement_id}/confirm",
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["stato"] == "confermata"

    # Riconfermare → 422
    resp2 = await client.post(
        f"/api/v1/clients/{d['client_id']}/fiscal-years/{d['fy_id']}/vat-settlements/{settlement_id}/confirm",
        headers=auth_headers,
    )
    assert resp2.status_code == 422


# ── Test 5: confermata → versata ──────────────────────────────────────────────

async def test_mark_versata(
    client: AsyncClient, auth_headers: dict, setup_base: dict
) -> None:
    """Liquidazione confermata può essere marcata versata con data e F24."""
    d = setup_base
    resp_compute = await client.post(
        f"/api/v1/clients/{d['client_id']}/fiscal-years/{d['fy_id']}/vat-settlements/compute",
        json={"periodo": "2024-01", "credito_precedente": "0"},
        headers=auth_headers,
    )
    settlement_id = resp_compute.json()["id"]

    # Conferma
    await client.post(
        f"/api/v1/clients/{d['client_id']}/fiscal-years/{d['fy_id']}/vat-settlements/{settlement_id}/confirm",
        headers=auth_headers,
    )

    # Marca versata
    resp = await client.post(
        f"/api/v1/clients/{d['client_id']}/fiscal-years/{d['fy_id']}/vat-settlements/{settlement_id}/mark-versata",
        json={"data_versamento": "2024-02-16", "f24_riferimento": "F24-2024-01-0001"},
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["stato"] == "versata"
    assert body["data_versamento"] == "2024-02-16"
    assert body["f24_riferimento"] == "F24-2024-01-0001"


# ── Test 6: prospetto F24 con codice tributo corretto ────────────────────────

async def test_f24_prospetto(
    client: AsyncClient, auth_headers: dict, setup_base: dict, db_session: AsyncSession
) -> None:
    """Gennaio mensile → codice 6001; Q1 trimestrale → codice 6031."""
    d = setup_base

    # Test mensile - gennaio
    resp_compute = await client.post(
        f"/api/v1/clients/{d['client_id']}/fiscal-years/{d['fy_id']}/vat-settlements/compute",
        json={"periodo": "2024-01", "credito_precedente": "0"},
        headers=auth_headers,
    )
    settlement_id = resp_compute.json()["id"]

    resp = await client.get(
        f"/api/v1/clients/{d['client_id']}/fiscal-years/{d['fy_id']}/vat-settlements/{settlement_id}/f24",
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["periodo"] == "2024-01"
    assert body["tipo_periodo"] == "mensile"
    assert len(body["sezione_erario"]) == 1
    assert body["sezione_erario"][0]["codice_tributo"] == "6001"
    assert Decimal(str(body["totale_saldo"])) == Decimal("300.00")

    # Crea registri IVA per Q1 (client separato)
    resp2 = await client.post("/api/v1/clients", json={
        "ragione_sociale": "Azienda Trim IVA SRL",
        "fiscal_regime": "ordinario",
        "periodicita_iva": "trimestrale",
    }, headers=auth_headers)
    c2_id = uuid.UUID(resp2.json()["id"])
    fy2_resp = await client.post(
        f"/api/v1/clients/{c2_id}/fiscal-years",
        json={"anno": 2024, "data_inizio": "2024-01-01", "data_fine": "2024-12-31"},
        headers=auth_headers,
    )
    fy2_id = uuid.UUID(fy2_resp.json()["id"])

    reg_v2 = VatRegister(id=uuid.uuid4(), studio_id=STUDIO_ID, client_entity_id=c2_id,
                          fiscal_year_id=fy2_id, tipo="vendite")
    db_session.add(reg_v2)
    je2 = JournalEntry(id=uuid.uuid4(), studio_id=STUDIO_ID, client_entity_id=c2_id,
                        fiscal_year_id=fy2_id, numero_registrazione=1,
                        data_registrazione=date(2024, 3, 31), descrizione="Vendita Q1",
                        causale="FV", stato="posted")
    db_session.add(je2)
    await db_session.flush()

    db_session.add(VatEntry(id=uuid.uuid4(), studio_id=STUDIO_ID, vat_register_id=reg_v2.id,
                             journal_entry_id=je2.id, data_documento=date(2024, 3, 31),
                             imponibile=Decimal("1000.00"), aliquota=22, imposta=Decimal("220.00")))
    await db_session.flush()

    resp_q1 = await client.post(
        f"/api/v1/clients/{c2_id}/fiscal-years/{fy2_id}/vat-settlements/compute",
        json={"periodo": "2024-Q1", "credito_precedente": "0"},
        headers=auth_headers,
    )
    s2_id = resp_q1.json()["id"]

    resp_f24_q1 = await client.get(
        f"/api/v1/clients/{c2_id}/fiscal-years/{fy2_id}/vat-settlements/{s2_id}/f24",
        headers=auth_headers,
    )
    assert resp_f24_q1.status_code == 200
    body_q1 = resp_f24_q1.json()
    assert body_q1["tipo_periodo"] == "trimestrale"
    assert body_q1["sezione_erario"][0]["codice_tributo"] == "6031"
