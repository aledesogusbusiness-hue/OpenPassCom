"""
Test Phase 3 — Ritenute d'acconto.
"""
import uuid
from datetime import date
from decimal import Decimal

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings

pytestmark = pytest.mark.asyncio

STUDIO_ID = uuid.UUID(settings.STUDIO_ID)


# ── Fixture base ──────────────────────────────────────────────────────────────

@pytest_asyncio.fixture()
async def setup_wt(client: AsyncClient, auth_headers: dict):
    """Cliente + esercizio per test ritenute."""
    resp = await client.post("/api/v1/clients", json={
        "ragione_sociale": "Studio Ritenute SRL",
        "fiscal_regime": "ordinario",
        "periodicita_iva": "mensile",
    }, headers=auth_headers)
    assert resp.status_code == 201, resp.text
    client_id = resp.json()["id"]

    fy_resp = await client.post(
        f"/api/v1/clients/{client_id}/fiscal-years",
        json={"anno": 2024, "data_inizio": "2024-01-01", "data_fine": "2024-12-31"},
        headers=auth_headers,
    )
    assert fy_resp.status_code == 201
    fy_id = fy_resp.json()["id"]

    return {"client_id": client_id, "fy_id": fy_id}


# ── Test 1: calcolo automatico importo ritenuta ───────────────────────────────

async def test_create_withholding(
    client: AsyncClient, auth_headers: dict, setup_wt: dict
) -> None:
    """20% di 1000 = 200.00 (arrotondato a 2 decimali)."""
    d = setup_wt
    url = f"/api/v1/clients/{d['client_id']}/fiscal-years/{d['fy_id']}/withholdings"

    resp = await client.post(url, json={
        "tipo": "professionale",
        "codice_tributo": "1040",
        "imponibile": "1000.00",
        "aliquota_pct": "20.00",
        "mese_competenza": 3,
        "anno_competenza": 2024,
    }, headers=auth_headers)

    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert Decimal(str(body["importo_ritenuta"])) == Decimal("200.00")
    assert body["tipo"] == "professionale"
    assert body["codice_tributo"] == "1040"
    assert body["stato"] == "da_versare"
    assert body["mese_competenza"] == 3
    assert body["anno_competenza"] == 2024

    # Verifica arrotondamento: 20% di 333.33 = 66.666 → 66.67
    resp2 = await client.post(url, json={
        "tipo": "occasionale",
        "imponibile": "333.33",
        "aliquota_pct": "20.00",
        "mese_competenza": 3,
        "anno_competenza": 2024,
    }, headers=auth_headers)
    assert resp2.status_code == 201
    # 333.33 * 20 / 100 = 66.666 → 66.67
    assert Decimal(str(resp2.json()["importo_ritenuta"])) == Decimal("66.67")


# ── Test 2: filtro per stato ──────────────────────────────────────────────────

async def test_list_withholdings_filter(
    client: AsyncClient, auth_headers: dict, setup_wt: dict
) -> None:
    """Lista ritenute filtrabile per stato da_versare / versata."""
    d = setup_wt
    url = f"/api/v1/clients/{d['client_id']}/fiscal-years/{d['fy_id']}/withholdings"

    # Crea 2 ritenute
    for importo in ["500.00", "800.00"]:
        r = await client.post(url, json={
            "tipo": "professionale",
            "imponibile": importo,
            "aliquota_pct": "20.00",
            "mese_competenza": 4,
            "anno_competenza": 2024,
        }, headers=auth_headers)
        assert r.status_code == 201

    # Senza filtro: entrambe
    resp_all = await client.get(url, headers=auth_headers)
    assert resp_all.status_code == 200
    items = resp_all.json()
    assert len(items) >= 2

    # Filtro da_versare
    resp_dv = await client.get(f"{url}?stato=da_versare", headers=auth_headers)
    assert resp_dv.status_code == 200
    assert all(i["stato"] == "da_versare" for i in resp_dv.json())

    # Filtro versata (nessuna ancora versata)
    resp_v = await client.get(f"{url}?stato=versata", headers=auth_headers)
    assert resp_v.status_code == 200
    assert len(resp_v.json()) == 0


# ── Test 3: mark versata ──────────────────────────────────────────────────────

async def test_mark_versata_withholding(
    client: AsyncClient, auth_headers: dict, setup_wt: dict
) -> None:
    """Ritenuta passa da da_versare a versata con data e riferimento F24."""
    d = setup_wt
    url = f"/api/v1/clients/{d['client_id']}/fiscal-years/{d['fy_id']}/withholdings"

    # Crea ritenuta
    resp_create = await client.post(url, json={
        "tipo": "autonomo",
        "imponibile": "2000.00",
        "aliquota_pct": "20.00",
        "mese_competenza": 5,
        "anno_competenza": 2024,
    }, headers=auth_headers)
    assert resp_create.status_code == 201
    wt_id = resp_create.json()["id"]

    # Marca versata
    resp = await client.post(
        f"{url}/{wt_id}/mark-versata",
        json={"data_versamento": "2024-06-17", "f24_riferimento": "RIT-2024-05-001"},
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["stato"] == "versata"
    assert body["data_versamento"] == "2024-06-17"
    assert body["f24_riferimento"] == "RIT-2024-05-001"


# ── Test 4: prospetto F24 ritenute per mese ───────────────────────────────────

async def test_f24_ritenute(
    client: AsyncClient, auth_headers: dict, setup_wt: dict
) -> None:
    """Prospetto F24 raggruppa ritenute per codice tributo nel mese."""
    d = setup_wt
    url = f"/api/v1/clients/{d['client_id']}/fiscal-years/{d['fy_id']}/withholdings"

    # 2 ritenute stesso mese, stesso codice: 200 + 300 = 500
    await client.post(url, json={
        "tipo": "professionale", "codice_tributo": "1040",
        "imponibile": "1000.00", "aliquota_pct": "20.00",
        "mese_competenza": 6, "anno_competenza": 2024,
    }, headers=auth_headers)
    await client.post(url, json={
        "tipo": "professionale", "codice_tributo": "1040",
        "imponibile": "1500.00", "aliquota_pct": "20.00",
        "mese_competenza": 6, "anno_competenza": 2024,
    }, headers=auth_headers)

    # Ritenuta mese diverso (non deve apparire)
    await client.post(url, json={
        "tipo": "professionale", "codice_tributo": "1040",
        "imponibile": "999.00", "aliquota_pct": "20.00",
        "mese_competenza": 7, "anno_competenza": 2024,
    }, headers=auth_headers)

    f24_url = f"/api/v1/clients/{d['client_id']}/fiscal-years/{d['fy_id']}/withholdings/f24"
    resp = await client.get(f"{f24_url}?mese=6&anno=2024", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["mese"] == 6
    assert body["anno"] == 2024
    assert len(body["righe"]) == 1
    assert body["righe"][0]["codice_tributo"] == "1040"
    # 20% di 1000 + 20% di 1500 = 200 + 300 = 500
    assert Decimal(str(body["totale"])) == Decimal("500.00")
