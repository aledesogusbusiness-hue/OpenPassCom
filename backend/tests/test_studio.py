"""
Test Phase 5 — Studio Dashboard e Task Management.

Fixtures:
- setup_studio: cliente base per i test
"""
import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings

pytestmark = pytest.mark.asyncio

STUDIO_ID = uuid.UUID(settings.STUDIO_ID)


# ── Fixture base ──────────────────────────────────────────────────────────────

@pytest_asyncio.fixture()
async def setup_studio(client: AsyncClient, auth_headers: dict):
    """Crea un cliente di base per i test studio."""
    resp = await client.post(
        "/api/v1/clients",
        json={
            "ragione_sociale": "Studio Test S.r.l.",
            "fiscal_regime": "ordinario",
            "periodicita_iva": "mensile",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    client_id = uuid.UUID(resp.json()["id"])
    return {"client_id": client_id}


# ── Test ──────────────────────────────────────────────────────────────────────

async def test_create_task(client: AsyncClient, auth_headers: dict, setup_studio: dict):
    """Verifica creazione di un task."""
    resp = await client.post(
        "/api/v1/tasks",
        json={
            "titolo": "Verifica dichiarazione IVA",
            "tipo": "scadenza_iva",
            "priorita": "alta",
            "data_scadenza": "2024-03-31",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["titolo"] == "Verifica dichiarazione IVA"
    assert data["tipo"] == "scadenza_iva"
    assert data["stato"] == "aperto"
    assert data["priorita"] == "alta"
    assert data["data_scadenza"] == "2024-03-31"


async def test_list_tasks_filter(client: AsyncClient, auth_headers: dict, setup_studio: dict):
    """Verifica filtro per stato e tipo."""
    # Crea due task con tipi diversi
    await client.post(
        "/api/v1/tasks",
        json={"titolo": "Task IVA filtro", "tipo": "scadenza_iva", "priorita": "normale"},
        headers=auth_headers,
    )
    await client.post(
        "/api/v1/tasks",
        json={"titolo": "Task Generico filtro", "tipo": "generico", "priorita": "bassa"},
        headers=auth_headers,
    )

    # Filtra per tipo=scadenza_iva
    resp = await client.get("/api/v1/tasks?tipo=scadenza_iva", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data) >= 1
    assert all(t["tipo"] == "scadenza_iva" for t in data)

    # Filtra per stato=aperto
    resp = await client.get("/api/v1/tasks?stato=aperto", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data) >= 2
    assert all(t["stato"] == "aperto" for t in data)


async def test_complete_task(client: AsyncClient, auth_headers: dict, setup_studio: dict):
    """Verifica completamento task."""
    resp = await client.post(
        "/api/v1/tasks",
        json={"titolo": "Task da completare", "tipo": "generico", "priorita": "normale"},
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    task_id = resp.json()["id"]

    resp = await client.post(
        f"/api/v1/tasks/{task_id}/complete",
        json={"completato_il": "2024-03-15"},
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["stato"] == "completato"
    assert data["completato_il"] == "2024-03-15"


async def test_cancel_task(client: AsyncClient, auth_headers: dict, setup_studio: dict):
    """Verifica annullamento task."""
    resp = await client.post(
        "/api/v1/tasks",
        json={"titolo": "Task da annullare", "tipo": "generico", "priorita": "bassa"},
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    task_id = resp.json()["id"]

    resp = await client.post(
        f"/api/v1/tasks/{task_id}/cancel",
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["stato"] == "annullato"


async def test_dashboard_summary(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession
):
    """Verifica che la dashboard restituisca i contatori corretti."""
    resp = await client.get("/api/v1/dashboard", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()

    # Verifica presenza di tutti i campi
    assert "clienti_attivi" in data
    assert "task_aperti" in data
    assert "task_urgenti" in data
    assert "scadenze_questa_settimana" in data
    assert "liquidazioni_bozza" in data
    assert "ritenute_da_versare" in data
    assert "fatture_importate" in data

    # Tutti i valori devono essere interi non negativi
    for key, val in data.items():
        assert isinstance(val, int), f"{key} deve essere int, got {type(val)}"
        assert val >= 0, f"{key} deve essere >= 0, got {val}"


async def test_generate_scadenzario_tasks(
    client: AsyncClient, auth_headers: dict, setup_studio: dict
):
    """Verifica che generate-scadenzario restituisca una lista (può essere vuota)."""
    resp = await client.post(
        "/api/v1/tasks/generate-scadenzario",
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert isinstance(data, list)

    # Se ci sono task generati, verificano la struttura base
    for task in data:
        assert "id" in task
        assert "tipo" in task
        assert "stato" in task
        assert task["stato"] == "aperto"
