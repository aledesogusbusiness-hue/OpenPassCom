"""
Test Phase 8 — Gestione utenti (solo admin).
"""
import uuid

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def _create_accountant(client: AsyncClient, auth_headers: dict, email: str = None) -> dict:
    email = email or f"acc-{uuid.uuid4().hex[:8]}@test.it"
    resp = await client.post(
        "/api/v1/users",
        json={
            "email": email,
            "password": "Password123!",
            "full_name": "Mario Contabile",
            "role": "accountant",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _login(client: AsyncClient, email: str, password: str) -> dict:
    resp = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def test_admin_can_list_users(client: AsyncClient, auth_headers: dict):
    resp = await client.get("/api/v1/users", headers=auth_headers)
    assert resp.status_code == 200
    emails = [u["email"] for u in resp.json()]
    assert "admin@test.it" in emails


async def test_admin_can_create_user(client: AsyncClient, auth_headers: dict):
    user = await _create_accountant(client, auth_headers, "nuovo@test.it")
    assert user["email"] == "nuovo@test.it"
    assert user["role"] == "accountant"
    assert user["is_active"] is True


async def test_duplicate_email_conflict(client: AsyncClient, auth_headers: dict):
    await _create_accountant(client, auth_headers, "dup@test.it")
    resp = await client.post(
        "/api/v1/users",
        json={
            "email": "dup@test.it",
            "password": "Password123!",
            "full_name": "Altro",
            "role": "accountant",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 409


async def test_new_user_can_login(client: AsyncClient, auth_headers: dict):
    user = await _create_accountant(client, auth_headers, "login-test@test.it")
    headers = await _login(client, "login-test@test.it", "Password123!")
    me_resp = await client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["id"] == user["id"]


async def test_admin_can_update_user(client: AsyncClient, auth_headers: dict):
    user = await _create_accountant(client, auth_headers)
    resp = await client.patch(
        f"/api/v1/users/{user['id']}",
        json={"full_name": "Nome Aggiornato", "role": "collaborator"},
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["full_name"] == "Nome Aggiornato"
    assert resp.json()["role"] == "collaborator"


async def test_admin_can_deactivate_user(client: AsyncClient, auth_headers: dict):
    user = await _create_accountant(client, auth_headers)
    resp = await client.delete(f"/api/v1/users/{user['id']}", headers=auth_headers)
    assert resp.status_code == 204

    list_resp = await client.get("/api/v1/users", headers=auth_headers)
    active_ids = [u["id"] for u in list_resp.json()]
    assert user["id"] not in active_ids

    list_all_resp = await client.get(
        "/api/v1/users?include_inactive=true", headers=auth_headers
    )
    all_ids = [u["id"] for u in list_all_resp.json()]
    assert user["id"] in all_ids


async def test_deactivated_user_cannot_login(client: AsyncClient, auth_headers: dict):
    user = await _create_accountant(client, auth_headers, "todeactivate@test.it")
    await client.delete(f"/api/v1/users/{user['id']}", headers=auth_headers)

    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "todeactivate@test.it", "password": "Password123!"},
    )
    assert resp.status_code == 401


async def test_admin_cannot_deactivate_self(client: AsyncClient, auth_headers: dict):
    me_resp = await client.get("/api/v1/auth/me", headers=auth_headers)
    my_id = me_resp.json()["id"]
    resp = await client.delete(f"/api/v1/users/{my_id}", headers=auth_headers)
    assert resp.status_code == 409


async def test_admin_cannot_remove_own_admin_role(client: AsyncClient, auth_headers: dict):
    me_resp = await client.get("/api/v1/auth/me", headers=auth_headers)
    my_id = me_resp.json()["id"]
    resp = await client.patch(
        f"/api/v1/users/{my_id}", json={"role": "accountant"}, headers=auth_headers
    )
    assert resp.status_code == 409


async def test_non_admin_cannot_list_users(client: AsyncClient, auth_headers: dict):
    user = await _create_accountant(client, auth_headers, "nonadmin1@test.it")
    headers = await _login(client, "nonadmin1@test.it", "Password123!")
    resp = await client.get("/api/v1/users", headers=headers)
    assert resp.status_code == 403


async def test_non_admin_cannot_create_users(client: AsyncClient, auth_headers: dict):
    await _create_accountant(client, auth_headers, "nonadmin2@test.it")
    headers = await _login(client, "nonadmin2@test.it", "Password123!")
    resp = await client.post(
        "/api/v1/users",
        json={
            "email": "hacker@test.it",
            "password": "Password123!",
            "full_name": "Hacker",
            "role": "admin",
        },
        headers=headers,
    )
    assert resp.status_code == 403
