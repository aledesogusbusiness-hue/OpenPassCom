"""
Test Phase 6 — Conservatore digitale.

Fixtures:
- setup_cons: cliente base per i test conservatore
"""
import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


# ── Fixture base ──────────────────────────────────────────────────────────────

@pytest_asyncio.fixture()
async def setup_cons(client: AsyncClient, auth_headers: dict):
    """Crea un cliente base per i test conservatore."""
    resp = await client.post(
        "/api/v1/clients",
        json={
            "ragione_sociale": "Conservatore Test S.r.l.",
            "fiscal_regime": "ordinario",
            "periodicita_iva": "mensile",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    return {"client_id": uuid.UUID(resp.json()["id"])}


# ── Test ──────────────────────────────────────────────────────────────────────

async def test_create_log(client: AsyncClient, auth_headers: dict, setup_cons: dict):
    """Verifica creazione log conservatore."""
    client_id = setup_cons["client_id"]
    resp = await client.post(
        f"/api/v1/clients/{client_id}/conservatore-logs",
        json={
            "tipo_documento": "libro_giornale",
            "periodo": "2024-Q1",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["tipo_documento"] == "libro_giornale"
    assert data["stato"] == "da_inviare"
    assert data["client_entity_id"] == str(client_id)
    assert data["periodo"] == "2024-Q1"


async def test_mark_inviato(client: AsyncClient, auth_headers: dict, setup_cons: dict):
    """Verifica transizione da_inviare → inviato."""
    client_id = setup_cons["client_id"]

    resp = await client.post(
        f"/api/v1/clients/{client_id}/conservatore-logs",
        json={"tipo_documento": "registro_iva"},
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    log_id = resp.json()["id"]

    resp = await client.post(
        f"/api/v1/clients/{client_id}/conservatore-logs/{log_id}/mark-inviato",
        json={"data_invio": "2024-04-01", "riferimento_esterno": "PROT-2024-001"},
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["stato"] == "inviato"
    assert data["riferimento_esterno"] == "PROT-2024-001"
    assert data["data_invio"] == "2024-04-01"


async def test_mark_confermato(client: AsyncClient, auth_headers: dict, setup_cons: dict):
    """Verifica transizione inviato → confermato."""
    client_id = setup_cons["client_id"]

    resp = await client.post(
        f"/api/v1/clients/{client_id}/conservatore-logs",
        json={"tipo_documento": "bilancio", "periodo": "2024"},
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    log_id = resp.json()["id"]

    # Prima mark-inviato
    await client.post(
        f"/api/v1/clients/{client_id}/conservatore-logs/{log_id}/mark-inviato",
        json={"data_invio": "2024-05-01"},
        headers=auth_headers,
    )

    # Poi mark-confermato
    resp = await client.post(
        f"/api/v1/clients/{client_id}/conservatore-logs/{log_id}/mark-confermato",
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["stato"] == "confermato"


async def test_mark_errore(client: AsyncClient, auth_headers: dict, setup_cons: dict):
    """Verifica transizione a stato errore (da qualsiasi stato)."""
    client_id = setup_cons["client_id"]

    resp = await client.post(
        f"/api/v1/clients/{client_id}/conservatore-logs",
        json={"tipo_documento": "libro_giornale"},
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    log_id = resp.json()["id"]

    resp = await client.post(
        f"/api/v1/clients/{client_id}/conservatore-logs/{log_id}/mark-errore",
        json={"note": "Firma digitale non valida"},
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["stato"] == "errore"
    assert data["note"] == "Firma digitale non valida"
