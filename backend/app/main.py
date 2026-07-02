import uuid
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, AsyncSessionLocal
from app.middleware import StudioTenantMiddleware
from app.models.base import Base
from app.models import auth, parties, accounting  # noqa: F401
from app.routers import auth as auth_router, parties as parties_router, accounting as accounting_router

logger = logging.getLogger(__name__)


async def run_seed() -> None:
    """Esegue il seed iniziale del database se mancano dati."""
    from sqlalchemy import select, text
    from app.models.auth import User
    from app.models.accounting import AccountType
    from app.services.auth_service import hash_password

    async with AsyncSessionLocal() as db:
        # Controlla se l'admin esiste già
        result = await db.execute(select(User).where(User.email == settings.SEED_ADMIN_EMAIL))
        if result.scalar_one_or_none():
            logger.info("Seed già eseguito, skip.")
            return

        logger.info("Esecuzione seed iniziale...")
        studio_id = uuid.UUID(settings.STUDIO_ID)

        # Admin utente
        admin = User(
            id=uuid.uuid4(),
            studio_id=studio_id,
            email=settings.SEED_ADMIN_EMAIL,
            hashed_password=hash_password(settings.SEED_ADMIN_PASSWORD),
            full_name="Admin Studio Rossi",
            is_active=True,
            role="admin",
        )
        db.add(admin)

        # Tipi di conto standard italiani
        account_types = [
            AccountType(
                id=uuid.uuid4(), tipo_codice="SP-A", nome="Stato Patrimoniale Attivo", posizione_bilancio="Attivo"
            ),
            AccountType(
                id=uuid.uuid4(), tipo_codice="SP-P", nome="Stato Patrimoniale Passivo", posizione_bilancio="Passivo"
            ),
            AccountType(
                id=uuid.uuid4(), tipo_codice="CE-C", nome="Conto Economico Costi", posizione_bilancio="Costi"
            ),
            AccountType(
                id=uuid.uuid4(), tipo_codice="CE-R", nome="Conto Economico Ricavi", posizione_bilancio="Ricavi"
            ),
        ]
        for at in account_types:
            db.add(at)

        await db.commit()
        logger.info("Seed iniziale completato.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Crea le tabelle (in produzione usa alembic)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await run_seed()
    yield
    await engine.dispose()


app = FastAPI(
    title="Registro Contabilità API",
    version="1.0.0",
    description="Piattaforma contabile per studio di commercialisti italiano",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware studio tenant
app.add_middleware(StudioTenantMiddleware)

# Routers
app.include_router(auth_router.router)
app.include_router(parties_router.router)
app.include_router(accounting_router.router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "studio_id": settings.STUDIO_ID}
