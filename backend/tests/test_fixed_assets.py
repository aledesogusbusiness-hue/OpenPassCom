"""
Test Phase 4 — Cespiti e piani di ammortamento.

Fixtures:
- setup_asset: crea cliente + esercizio 2024 via API.
- setup_asset_direct: crea anche il cespite direttamente via service per test
  che richiedono accesso ai modelli ORM.
"""
import uuid
from decimal import Decimal

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.schemas.balance import FixedAssetCreate
from app.services.fixed_asset_service import (
    create_fixed_asset,
    compute_depreciation_plan,
    book_depreciation,
)

pytestmark = pytest.mark.asyncio

STUDIO_ID = uuid.UUID(settings.STUDIO_ID)

_ASSET_BODY = {
    "codice": "ATTR001",
    "descrizione": "Attrezzatura Test",
    "categoria": "Attrezzature",
    "costo_storico": "10000.00",
    "data_acquisto": "2024-03-15",
    "aliquota_ammortamento": "20.00",
    "metodo": "quote_costanti",
}


# ── Fixture base ─────────────────────────────────────────────────────────────

@pytest_asyncio.fixture()
async def setup_asset(client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
    """Crea cliente ordinario + esercizio 2024 via API."""
    resp = await client.post(
        "/api/v1/clients",
        json={
            "ragione_sociale": "Test Cespiti S.r.l.",
            "fiscal_regime": "ordinario",
            "periodicita_iva": "mensile",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    client_id = resp.json()["id"]

    fy_resp = await client.post(
        f"/api/v1/clients/{client_id}/fiscal-years",
        json={"anno": 2024, "data_inizio": "2024-01-01", "data_fine": "2024-12-31"},
        headers=auth_headers,
    )
    assert fy_resp.status_code == 201, fy_resp.text

    return {"client_id": client_id}


@pytest_asyncio.fixture()
async def setup_asset_direct(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession
):
    """Crea cliente + esercizio via API, poi cespite via service."""
    resp = await client.post(
        "/api/v1/clients",
        json={
            "ragione_sociale": "Test Cespiti Direct S.r.l.",
            "fiscal_regime": "ordinario",
            "periodicita_iva": "mensile",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    client_id = uuid.UUID(resp.json()["id"])

    fy_resp = await client.post(
        f"/api/v1/clients/{client_id}/fiscal-years",
        json={"anno": 2024, "data_inizio": "2024-01-01", "data_fine": "2024-12-31"},
        headers=auth_headers,
    )
    assert fy_resp.status_code == 201, fy_resp.text

    # Crea cespite direttamente via service (stessa db_session)
    data = FixedAssetCreate(
        codice="CESPDIRECT",
        descrizione="Cespite Direct",
        categoria="Attrezzature",
        costo_storico=Decimal("10000.00"),
        data_acquisto="2024-01-01",
        aliquota_ammortamento=Decimal("20.00"),
        metodo="quote_costanti",
    )
    asset = await create_fixed_asset(db_session, client_id, data, uuid.uuid4())
    return {"client_id": str(client_id), "asset": asset}


# ── Test CRUD ────────────────────────────────────────────────────────────────

async def test_create_fixed_asset(
    client: AsyncClient, auth_headers: dict, setup_asset: dict
):
    """Crea cespite → 201, dati corretti."""
    client_id = setup_asset["client_id"]
    resp = await client.post(
        f"/api/v1/clients/{client_id}/fixed-assets",
        json=_ASSET_BODY,
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["codice"] == "ATTR001"
    assert data["categoria"] == "Attrezzature"
    assert Decimal(data["costo_storico"]) == Decimal("10000.00")
    assert Decimal(data["aliquota_ammortamento"]) == Decimal("20.00")
    assert data["metodo"] == "quote_costanti"
    assert data["is_active"] is True


async def test_list_fixed_assets(
    client: AsyncClient, auth_headers: dict, setup_asset: dict
):
    """Lista cespiti: solo attivi per default, include_inactive=true mostra tutti."""
    client_id = setup_asset["client_id"]

    # Crea due cespiti
    await client.post(
        f"/api/v1/clients/{client_id}/fixed-assets",
        json={**_ASSET_BODY, "codice": "LST001"},
        headers=auth_headers,
    )
    r2 = await client.post(
        f"/api/v1/clients/{client_id}/fixed-assets",
        json={**_ASSET_BODY, "codice": "LST002"},
        headers=auth_headers,
    )
    asset2_id = r2.json()["id"]

    # Disattiva il secondo
    await client.delete(
        f"/api/v1/clients/{client_id}/fixed-assets/{asset2_id}",
        headers=auth_headers,
    )

    # Lista default: solo attivi
    lst = await client.get(
        f"/api/v1/clients/{client_id}/fixed-assets",
        headers=auth_headers,
    )
    assert lst.status_code == 200
    ids = [a["id"] for a in lst.json()]
    assert asset2_id not in ids

    # Lista con include_inactive=true
    lst_all = await client.get(
        f"/api/v1/clients/{client_id}/fixed-assets?include_inactive=true",
        headers=auth_headers,
    )
    ids_all = [a["id"] for a in lst_all.json()]
    assert asset2_id in ids_all


async def test_deactivate_fixed_asset(
    client: AsyncClient, auth_headers: dict, setup_asset: dict
):
    """DELETE su cespite → soft delete, is_active=False."""
    client_id = setup_asset["client_id"]

    cr = await client.post(
        f"/api/v1/clients/{client_id}/fixed-assets",
        json={**_ASSET_BODY, "codice": "DEL001"},
        headers=auth_headers,
    )
    asset_id = cr.json()["id"]

    del_resp = await client.delete(
        f"/api/v1/clients/{client_id}/fixed-assets/{asset_id}",
        headers=auth_headers,
    )
    assert del_resp.status_code == 204

    # Verifica che non appaia nella lista di default
    lst = await client.get(
        f"/api/v1/clients/{client_id}/fixed-assets",
        headers=auth_headers,
    )
    ids = [a["id"] for a in lst.json()]
    assert asset_id not in ids


# ── Test ammortamento: quote costanti ────────────────────────────────────────

async def test_compute_depreciation_plan_quote_costanti(
    client: AsyncClient, auth_headers: dict, setup_asset: dict
):
    """
    Piano ammortamento quote costanti con regola del semestre:
    - Anno 1: quota = 10000 * 20% * 0.5 = 1000.00
    - Anni 2+: quota = 10000 * 20% = 2000.00
    - Stop quando valore_netto_finale <= 0
    """
    client_id = setup_asset["client_id"]

    cr = await client.post(
        f"/api/v1/clients/{client_id}/fixed-assets",
        json={**_ASSET_BODY, "codice": "QC001"},
        headers=auth_headers,
    )
    assert cr.status_code == 201
    asset_id = cr.json()["id"]

    plan_resp = await client.post(
        f"/api/v1/clients/{client_id}/fixed-assets/{asset_id}/compute-plan?anni=10",
        headers=auth_headers,
    )
    assert plan_resp.status_code == 200, plan_resp.text
    plan = plan_resp.json()

    assert len(plan) > 0

    # Anno 1: regola del semestre → 1000.00
    y1 = plan[0]
    assert y1["anno"] == 2024
    assert Decimal(y1["quota_ammortamento"]) == Decimal("1000.00")
    assert Decimal(y1["valore_iniziale"]) == Decimal("10000.00")
    assert Decimal(y1["fondo_ammortamento"]) == Decimal("1000.00")
    assert Decimal(y1["valore_netto_finale"]) == Decimal("9000.00")
    assert y1["stato"] == "calcolato"

    # Anno 2: quota piena → 2000.00
    y2 = plan[1]
    assert y2["anno"] == 2025
    assert Decimal(y2["quota_ammortamento"]) == Decimal("2000.00")
    assert Decimal(y2["valore_iniziale"]) == Decimal("9000.00")

    # L'ultimo anno ha valore_netto_finale = 0
    last = plan[-1]
    assert Decimal(last["valore_netto_finale"]) == Decimal("0.00")

    # Con 20% quote costanti + semestre: 6 anni totali
    # y1:1000, y2:2000, y3:2000, y4:2000, y5:2000, y6:1000(residuo) → 6 anni
    assert len(plan) == 6


async def test_compute_depreciation_plan_decrescente(
    client: AsyncClient, auth_headers: dict, setup_asset: dict
):
    """
    Piano ammortamento decrescente (double declining):
    - Anno 1: quota = 10000 * 20% * 2 = 4000.00
    - Anno 2: quota = 6000 * 20% * 2 = 2400.00
    """
    client_id = setup_asset["client_id"]

    cr = await client.post(
        f"/api/v1/clients/{client_id}/fixed-assets",
        json={
            **_ASSET_BODY,
            "codice": "DEC001",
            "metodo": "decrescente",
        },
        headers=auth_headers,
    )
    assert cr.status_code == 201
    asset_id = cr.json()["id"]

    plan_resp = await client.post(
        f"/api/v1/clients/{client_id}/fixed-assets/{asset_id}/compute-plan?anni=10",
        headers=auth_headers,
    )
    assert plan_resp.status_code == 200, plan_resp.text
    plan = plan_resp.json()

    assert len(plan) > 0

    # Anno 1: valore_iniziale=10000, quota=10000*0.40=4000
    y1 = plan[0]
    assert y1["anno"] == 2024
    assert Decimal(y1["quota_ammortamento"]) == Decimal("4000.00")
    assert Decimal(y1["valore_iniziale"]) == Decimal("10000.00")
    assert Decimal(y1["fondo_ammortamento"]) == Decimal("4000.00")
    assert Decimal(y1["valore_netto_finale"]) == Decimal("6000.00")

    # Anno 2: valore_iniziale=6000, quota=6000*0.40=2400
    y2 = plan[1]
    assert y2["anno"] == 2025
    assert Decimal(y2["quota_ammortamento"]) == Decimal("2400.00")
    assert Decimal(y2["valore_iniziale"]) == Decimal("6000.00")

    # Tutti calcolati
    for y in plan:
        assert y["stato"] == "calcolato"


# ── Test registro cespiti ────────────────────────────────────────────────────

async def test_registro_cespiti(
    client: AsyncClient, auth_headers: dict, setup_asset: dict
):
    """Registro cespiti per anno: mostra quota/fondo/netto per i cespiti attivi."""
    client_id = setup_asset["client_id"]

    # Crea cespite
    cr = await client.post(
        f"/api/v1/clients/{client_id}/fixed-assets",
        json={**_ASSET_BODY, "codice": "REG001"},
        headers=auth_headers,
    )
    asset_id = cr.json()["id"]

    # Calcola piano (anno 2024)
    await client.post(
        f"/api/v1/clients/{client_id}/fixed-assets/{asset_id}/compute-plan?anni=5",
        headers=auth_headers,
    )

    # Registro cespiti anno 2024
    reg_resp = await client.get(
        f"/api/v1/clients/{client_id}/registro-cespiti?anno=2024",
        headers=auth_headers,
    )
    assert reg_resp.status_code == 200, reg_resp.text
    rows = reg_resp.json()

    assert len(rows) >= 1
    # Trova la riga del nostro cespite
    row = next((r for r in rows if r["asset"]["codice"] == "REG001"), None)
    assert row is not None
    assert Decimal(row["quota_anno"]) == Decimal("1000.00")  # semestre
    assert Decimal(row["fondo_cumulato"]) == Decimal("1000.00")
    assert Decimal(row["valore_netto"]) == Decimal("9000.00")

    # Anno senza piano: valori None
    reg_resp_empty = await client.get(
        f"/api/v1/clients/{client_id}/registro-cespiti?anno=2099",
        headers=auth_headers,
    )
    assert reg_resp_empty.status_code == 200
    rows_empty = reg_resp_empty.json()
    row_empty = next((r for r in rows_empty if r["asset"]["codice"] == "REG001"), None)
    assert row_empty is not None
    assert row_empty["quota_anno"] is None


# ── Test book depreciation ───────────────────────────────────────────────────

async def test_book_depreciation(
    db_session: AsyncSession, setup_asset_direct: dict
):
    """book_depreciation imposta stato='contabilizzato' e collega il journal_entry_id."""
    asset = setup_asset_direct["asset"]

    # Calcola piano
    entries = await compute_depreciation_plan(db_session, asset, anni=3)
    assert len(entries) > 0

    entry = entries[0]
    assert entry.stato == "calcolato"

    # Contabilizza con un journal_entry_id fittizio
    fake_journal_id = uuid.uuid4()
    booked = await book_depreciation(db_session, entry, fake_journal_id)

    assert booked.stato == "contabilizzato"
    assert booked.journal_entry_id == fake_journal_id

    # Ricalcola: l'entry contabilizzata NON deve essere sovrascritta
    entries2 = await compute_depreciation_plan(db_session, asset, anni=3)
    contabilizzato = next((e for e in entries2 if e.anno == entry.anno), None)
    assert contabilizzato is not None
    assert contabilizzato.stato == "contabilizzato"
    assert contabilizzato.journal_entry_id == fake_journal_id
