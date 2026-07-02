import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

CLIENT_ORDINARIO = {
    "ragione_sociale": "Impianti Test S.r.l.",
    "codice_fiscale": "TSTCMP80A01H501Z",
    "partita_iva": "12345678901",
    "fiscal_regime": "ordinario",
    "periodicita_iva": "mensile",
}

FISCAL_YEAR_2025 = {
    "anno": 2025,
    "data_inizio": "2025-01-01",
    "data_fine": "2025-12-31",
}


async def test_create_client(client: AsyncClient, auth_headers: dict) -> None:
    """Crea cliente → 201, i dati sono corretti."""
    resp = await client.post("/api/v1/clients", json=CLIENT_ORDINARIO, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["ragione_sociale"] == CLIENT_ORDINARIO["ragione_sociale"]
    assert data["fiscal_regime"] == "ordinario"
    assert data["is_active"] is True


async def test_get_client(client: AsyncClient, auth_headers: dict) -> None:
    """Crea cliente, poi recuperalo per ID → 200."""
    create = await client.post("/api/v1/clients", json={
        **CLIENT_ORDINARIO,
        "partita_iva": "99988877701",
    }, headers=auth_headers)
    assert create.status_code == 201
    client_id = create.json()["id"]

    get = await client.get(f"/api/v1/clients/{client_id}", headers=auth_headers)
    assert get.status_code == 200
    assert get.json()["id"] == client_id


async def test_soft_delete_client(client: AsyncClient, auth_headers: dict) -> None:
    """Soft delete: is_active=False, non appare nella lista default."""
    create = await client.post("/api/v1/clients", json={
        **CLIENT_ORDINARIO,
        "partita_iva": "11122233301",
    }, headers=auth_headers)
    assert create.status_code == 201
    client_id = create.json()["id"]

    # Disattiva
    del_resp = await client.delete(f"/api/v1/clients/{client_id}", headers=auth_headers)
    assert del_resp.status_code == 204

    # Non deve apparire nella lista di default
    lst = await client.get("/api/v1/clients", headers=auth_headers)
    ids = [c["id"] for c in lst.json()]
    assert client_id not in ids

    # Ma deve apparire con include_inactive=true
    lst_all = await client.get("/api/v1/clients?include_inactive=true", headers=auth_headers)
    ids_all = [c["id"] for c in lst_all.json()]
    assert client_id in ids_all

    # Verifica is_active=False
    get = await client.get(f"/api/v1/clients/{client_id}", headers=auth_headers)
    assert get.json()["is_active"] is False


async def test_create_fiscal_year(client: AsyncClient, auth_headers: dict) -> None:
    """Crea esercizio fiscale → 201."""
    create = await client.post("/api/v1/clients", json={
        **CLIENT_ORDINARIO,
        "partita_iva": "44455566601",
    }, headers=auth_headers)
    assert create.status_code == 201
    client_id = create.json()["id"]

    fy_resp = await client.post(
        f"/api/v1/clients/{client_id}/fiscal-years",
        json=FISCAL_YEAR_2025,
        headers=auth_headers,
    )
    assert fy_resp.status_code == 201
    data = fy_resp.json()
    assert data["anno"] == 2025
    assert data["stato"] == "aperto"
    assert data["client_entity_id"] == client_id


async def test_close_fiscal_year(client: AsyncClient, auth_headers: dict) -> None:
    """Chiudi esercizio → stato='chiuso'."""
    create = await client.post("/api/v1/clients", json={
        **CLIENT_ORDINARIO,
        "partita_iva": "77788899901",
    }, headers=auth_headers)
    client_id = create.json()["id"]

    fy_resp = await client.post(
        f"/api/v1/clients/{client_id}/fiscal-years",
        json=FISCAL_YEAR_2025,
        headers=auth_headers,
    )
    year_id = fy_resp.json()["id"]

    close = await client.post(
        f"/api/v1/clients/{client_id}/fiscal-years/{year_id}/close",
        headers=auth_headers,
    )
    assert close.status_code == 200
    assert close.json()["stato"] == "chiuso"


async def test_duplicate_fiscal_year(client: AsyncClient, auth_headers: dict) -> None:
    """Esercizio duplicato (stesso anno, stesso cliente) → 409."""
    create = await client.post("/api/v1/clients", json={
        **CLIENT_ORDINARIO,
        "partita_iva": "55566677701",
    }, headers=auth_headers)
    client_id = create.json()["id"]

    first = await client.post(
        f"/api/v1/clients/{client_id}/fiscal-years",
        json=FISCAL_YEAR_2025,
        headers=auth_headers,
    )
    assert first.status_code == 201

    second = await client.post(
        f"/api/v1/clients/{client_id}/fiscal-years",
        json=FISCAL_YEAR_2025,
        headers=auth_headers,
    )
    assert second.status_code == 409
    assert "già esistente" in second.json()["detail"]


async def test_forfettario_no_periodicita_iva(client: AsyncClient, auth_headers: dict) -> None:
    """Regime forfettario non deve avere periodicità IVA."""
    resp = await client.post("/api/v1/clients", json={
        "ragione_sociale": "Artigiano Test",
        "fiscal_regime": "forfettario",
        "periodicita_iva": "mensile",  # non valido per forfettario
    }, headers=auth_headers)
    assert resp.status_code == 422
