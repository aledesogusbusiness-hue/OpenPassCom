import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_login_success(client: AsyncClient) -> None:
    """Login con credenziali corrette restituisce 200 e access_token."""
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.it", "password": "TestPass123!"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] > 0


async def test_login_wrong_password(client: AsyncClient) -> None:
    """Login con password errata restituisce 401."""
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.it", "password": "sbagliata"},
    )
    assert resp.status_code == 401
    assert "detail" in resp.json()


async def test_login_unknown_user(client: AsyncClient) -> None:
    """Login con email inesistente restituisce 401."""
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "nessuno@test.it", "password": "qualsiasi"},
    )
    assert resp.status_code == 401


async def test_me_without_token(client: AsyncClient) -> None:
    """/me senza token restituisce 403 (HTTPBearer rifiuta)."""
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code in (401, 403)


async def test_me_with_valid_token(client: AsyncClient, auth_headers: dict) -> None:
    """/me con token valido restituisce 200 e dati utente."""
    resp = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "admin@test.it"
    assert data["role"] == "admin"
    assert data["is_active"] is True
