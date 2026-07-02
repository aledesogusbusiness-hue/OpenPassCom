"""
conftest.py — Fixtures di test per Registro Contabilità.

Usa SQLite in-memoria con StaticPool per isolare i test dall'istanza PostgreSQL
di produzione. Il seed del database (AccountType + utente admin) viene eseguito
una sola volta a livello di modulo.
"""
import asyncio
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.database import get_db
from app.main import app
from app.models.base import Base
from app.models import auth, parties, accounting  # noqa: F401
from app.models.auth import User
from app.models.accounting import AccountType
from app.services.auth_service import hash_password

# ─── Database di test (SQLite in-memory, connessione unica via StaticPool) ────

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

STUDIO_ID = uuid.UUID(settings.STUDIO_ID)
ADMIN_EMAIL = "admin@test.it"
ADMIN_PASSWORD = "TestPass123!"

# ─── Setup del DB (una sola volta per l'intero processo di test) ────────────

_db_lock = asyncio.Lock()
_db_initialized = False


async def _ensure_db_ready() -> None:
    """Crea schema e inserisce seed (idempotente, thread-safe via lock)."""
    global _db_initialized
    if _db_initialized:
        return

    async with _db_lock:
        if _db_initialized:
            return

        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with TestSessionLocal() as db:
            for at in [
                AccountType(id=uuid.UUID("10000000-0000-0000-0000-000000000001"),
                            tipo_codice="SP-A", nome="Stato Patrimoniale Attivo", posizione_bilancio="Attivo"),
                AccountType(id=uuid.UUID("10000000-0000-0000-0000-000000000002"),
                            tipo_codice="SP-P", nome="Stato Patrimoniale Passivo", posizione_bilancio="Passivo"),
                AccountType(id=uuid.UUID("10000000-0000-0000-0000-000000000003"),
                            tipo_codice="CE-C", nome="Conto Economico Costi", posizione_bilancio="Costi"),
                AccountType(id=uuid.UUID("10000000-0000-0000-0000-000000000004"),
                            tipo_codice="CE-R", nome="Conto Economico Ricavi", posizione_bilancio="Ricavi"),
            ]:
                await db.merge(at)

            res = await db.execute(select(User).where(User.email == ADMIN_EMAIL))
            if not res.scalar_one_or_none():
                db.add(User(
                    id=uuid.uuid4(),
                    studio_id=STUDIO_ID,
                    email=ADMIN_EMAIL,
                    hashed_password=hash_password(ADMIN_PASSWORD),
                    full_name="Admin Test",
                    is_active=True,
                    role="admin",
                ))

            await db.commit()

        _db_initialized = True


# ─── Lifespan no-op per i test (evita connessione a PostgreSQL) ─────────────

@asynccontextmanager
async def _noop_lifespan(app_):
    yield


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture()
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    await _ensure_db_ready()
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture()
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    # Sostituisce il lifespan con un no-op per evitare connessione a PostgreSQL
    original_lifespan = app.router.lifespan_context
    app.router.lifespan_context = _noop_lifespan
    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=True),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
    app.router.lifespan_context = original_lifespan


@pytest_asyncio.fixture()
async def auth_headers(client: AsyncClient) -> dict:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    assert resp.status_code == 200, f"Login fallito: {resp.text}"
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
