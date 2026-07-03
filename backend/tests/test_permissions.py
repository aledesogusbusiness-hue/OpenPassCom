"""
Test Phase 8 — Permessi granulari per cliente.
"""
import uuid

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def _create_and_login_accountant(client: AsyncClient, auth_headers: dict) -> tuple[dict, dict]:
    email = f"acc-{uuid.uuid4().hex[:8]}@test.it"
    resp = await client.post(
        "/api/v1/users",
        json={
            "email": email,
            "password": "Password123!",
            "full_name": "Collaboratore Test",
            "role": "accountant",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    user = resp.json()

    login_resp = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "Password123!"}
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    return user, {"Authorization": f"Bearer {token}"}


async def _create_client(client: AsyncClient, auth_headers: dict, nome: str) -> str:
    resp = await client.post(
        "/api/v1/clients",
        json={
            "ragione_sociale": nome,
            "fiscal_regime": "ordinario",
            "periodicita_iva": "mensile",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def test_non_admin_sees_no_clients_without_permission(
    client: AsyncClient, auth_headers: dict
):
    await _create_client(client, auth_headers, "Cliente Senza Permesso")
    _, user_headers = await _create_and_login_accountant(client, auth_headers)

    resp = await client.get("/api/v1/clients", headers=user_headers)
    assert resp.status_code == 200
    assert resp.json() == []


async def test_non_admin_cannot_access_client_detail_without_permission(
    client: AsyncClient, auth_headers: dict
):
    client_id = await _create_client(client, auth_headers, "Cliente Bloccato")
    _, user_headers = await _create_and_login_accountant(client, auth_headers)

    resp = await client.get(f"/api/v1/clients/{client_id}", headers=user_headers)
    assert resp.status_code == 403


async def test_grant_lettura_allows_read_but_not_write(
    client: AsyncClient, auth_headers: dict
):
    client_id = await _create_client(client, auth_headers, "Cliente Lettura")
    user, user_headers = await _create_and_login_accountant(client, auth_headers)

    grant_resp = await client.post(
        f"/api/v1/clients/{client_id}/permissions",
        json={"user_id": user["id"], "permesso": "lettura"},
        headers=auth_headers,
    )
    assert grant_resp.status_code == 201, grant_resp.text
    assert grant_resp.json()["permesso"] == "lettura"

    # Lettura: GET consentito
    get_resp = await client.get(f"/api/v1/clients/{client_id}", headers=user_headers)
    assert get_resp.status_code == 200

    # Lettura: PUT negato
    put_resp = await client.put(
        f"/api/v1/clients/{client_id}",
        json={"note": "Tentativo di modifica"},
        headers=user_headers,
    )
    assert put_resp.status_code == 403


async def test_grant_scrittura_allows_read_and_write(
    client: AsyncClient, auth_headers: dict
):
    client_id = await _create_client(client, auth_headers, "Cliente Scrittura")
    user, user_headers = await _create_and_login_accountant(client, auth_headers)

    await client.post(
        f"/api/v1/clients/{client_id}/permissions",
        json={"user_id": user["id"], "permesso": "scrittura"},
        headers=auth_headers,
    )

    put_resp = await client.put(
        f"/api/v1/clients/{client_id}",
        json={"note": "Modifica consentita"},
        headers=user_headers,
    )
    assert put_resp.status_code == 200, put_resp.text
    assert put_resp.json()["note"] == "Modifica consentita"


async def test_revoke_permission_removes_access(client: AsyncClient, auth_headers: dict):
    client_id = await _create_client(client, auth_headers, "Cliente Revocato")
    user, user_headers = await _create_and_login_accountant(client, auth_headers)

    await client.post(
        f"/api/v1/clients/{client_id}/permissions",
        json={"user_id": user["id"], "permesso": "lettura"},
        headers=auth_headers,
    )
    ok_resp = await client.get(f"/api/v1/clients/{client_id}", headers=user_headers)
    assert ok_resp.status_code == 200

    revoke_resp = await client.delete(
        f"/api/v1/clients/{client_id}/permissions/{user['id']}", headers=auth_headers
    )
    assert revoke_resp.status_code == 204

    blocked_resp = await client.get(f"/api/v1/clients/{client_id}", headers=user_headers)
    assert blocked_resp.status_code == 403


async def test_non_admin_cannot_grant_permissions(client: AsyncClient, auth_headers: dict):
    client_id = await _create_client(client, auth_headers, "Cliente Protetto")
    user, user_headers = await _create_and_login_accountant(client, auth_headers)

    resp = await client.post(
        f"/api/v1/clients/{client_id}/permissions",
        json={"user_id": user["id"], "permesso": "scrittura"},
        headers=user_headers,
    )
    assert resp.status_code == 403


async def test_grant_permission_upserts_existing(client: AsyncClient, auth_headers: dict):
    """Concedere un permesso già esistente aggiorna il livello invece di duplicare."""
    client_id = await _create_client(client, auth_headers, "Cliente Upsert")
    user, _ = await _create_and_login_accountant(client, auth_headers)

    await client.post(
        f"/api/v1/clients/{client_id}/permissions",
        json={"user_id": user["id"], "permesso": "lettura"},
        headers=auth_headers,
    )
    second = await client.post(
        f"/api/v1/clients/{client_id}/permissions",
        json={"user_id": user["id"], "permesso": "scrittura"},
        headers=auth_headers,
    )
    assert second.status_code == 201

    list_resp = await client.get(
        f"/api/v1/clients/{client_id}/permissions", headers=auth_headers
    )
    perms = [p for p in list_resp.json() if p["user_id"] == user["id"]]
    assert len(perms) == 1
    assert perms[0]["permesso"] == "scrittura"


async def test_admin_bypasses_all_permission_checks(client: AsyncClient, auth_headers: dict):
    client_id = await _create_client(client, auth_headers, "Cliente Admin")
    resp = await client.get(f"/api/v1/clients/{client_id}", headers=auth_headers)
    assert resp.status_code == 200
