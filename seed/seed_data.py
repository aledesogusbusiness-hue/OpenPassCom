"""
Script di seed per il database di Registro Contabilità.

Uso:
  cd /home/user/registro-contabilita
  DATABASE_URL=postgresql+asyncpg://rcuser:rcpassword@localhost:5432/registro_contabilita \
  python seed/seed_data.py
"""
import asyncio
import os
import sys
import uuid
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select

from app.config import settings
from app.models.base import Base
from app.models.auth import User
from app.models.parties import ClientEntity, FiscalYear
from app.models.accounting import AccountPlan, AccountType, Account
from app.services.auth_service import hash_password

DATABASE_URL = os.environ.get("DATABASE_URL", settings.DATABASE_URL)
STUDIO_ID = uuid.UUID(settings.STUDIO_ID)

engine = create_async_engine(DATABASE_URL, echo=False)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# UUIDs fissi per riproducibilità
ADMIN_ID = uuid.UUID("20000000-0000-0000-0000-000000000001")
CLIENT_MELONI_ID = uuid.UUID("30000000-0000-0000-0000-000000000001")
CLIENT_PILIA_ID = uuid.UUID("30000000-0000-0000-0000-000000000002")
CLIENT_MURA_ID = uuid.UUID("30000000-0000-0000-0000-000000000003")
PLAN_MELONI_ID = uuid.UUID("40000000-0000-0000-0000-000000000001")

AT_SP_A = uuid.UUID("10000000-0000-0000-0000-000000000001")
AT_SP_P = uuid.UUID("10000000-0000-0000-0000-000000000002")
AT_CE_C = uuid.UUID("10000000-0000-0000-0000-000000000003")
AT_CE_R = uuid.UUID("10000000-0000-0000-0000-000000000004")

# Piano dei conti standard italiano (struttura semplificata)
PIANO_CONTI = [
    # Stato Patrimoniale Attivo
    (AT_SP_A, "01", "Immobilizzazioni", 1, None),
    (AT_SP_A, "01.01", "Immobilizzazioni immateriali", 2, "01"),
    (AT_SP_A, "01.02", "Immobilizzazioni materiali", 2, "01"),
    (AT_SP_A, "01.03", "Immobilizzazioni finanziarie", 2, "01"),
    (AT_SP_A, "02", "Attivo circolante", 1, None),
    (AT_SP_A, "02.01", "Rimanenze", 2, "02"),
    (AT_SP_A, "02.02", "Crediti commerciali", 2, "02"),
    (AT_SP_A, "02.03", "Disponibilità liquide", 2, "02"),
    (AT_SP_A, "02.04", "Attività finanziarie a breve", 2, "02"),
    (AT_SP_A, "03", "Ratei e risconti attivi", 1, None),
    # Stato Patrimoniale Passivo
    (AT_SP_P, "10", "Patrimonio netto", 1, None),
    (AT_SP_P, "10.01", "Capitale sociale", 2, "10"),
    (AT_SP_P, "10.02", "Riserve", 2, "10"),
    (AT_SP_P, "10.03", "Utile / perdita d'esercizio", 2, "10"),
    (AT_SP_P, "11", "Fondi per rischi e oneri", 1, None),
    (AT_SP_P, "12", "TFR", 1, None),
    (AT_SP_P, "13", "Debiti", 1, None),
    (AT_SP_P, "13.01", "Debiti verso banche", 2, "13"),
    (AT_SP_P, "13.02", "Debiti commerciali", 2, "13"),
    (AT_SP_P, "13.03", "Debiti tributari", 2, "13"),
    (AT_SP_P, "13.04", "Debiti previdenziali", 2, "13"),
    (AT_SP_P, "14", "Ratei e risconti passivi", 1, None),
    # Conto Economico Costi
    (AT_CE_C, "20", "Costi della produzione", 1, None),
    (AT_CE_C, "20.01", "Acquisto materie prime", 2, "20"),
    (AT_CE_C, "20.02", "Costi per servizi", 2, "20"),
    (AT_CE_C, "20.03", "Costi per godimento beni di terzi", 2, "20"),
    (AT_CE_C, "20.04", "Costi del personale", 2, "20"),
    (AT_CE_C, "20.05", "Ammortamenti", 2, "20"),
    (AT_CE_C, "20.06", "Oneri diversi di gestione", 2, "20"),
    (AT_CE_C, "21", "Proventi e oneri finanziari (oneri)", 1, None),
    (AT_CE_C, "22", "Rettifiche di valore attività finanziarie (neg)", 1, None),
    (AT_CE_C, "23", "Imposte sul reddito", 1, None),
    # Conto Economico Ricavi
    (AT_CE_R, "30", "Valore della produzione", 1, None),
    (AT_CE_R, "30.01", "Ricavi delle vendite", 2, "30"),
    (AT_CE_R, "30.02", "Variazione rimanenze prodotti", 2, "30"),
    (AT_CE_R, "30.03", "Altri ricavi e proventi", 2, "30"),
    (AT_CE_R, "31", "Proventi finanziari", 1, None),
    (AT_CE_R, "32", "Rettifiche di valore attività finanziarie (pos)", 1, None),
]


async def main() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as db:
        # Controlla seed già eseguito
        result = await db.execute(select(User).where(User.email == settings.SEED_ADMIN_EMAIL))
        if result.scalar_one_or_none():
            print("Seed già eseguito. Uscita.")
            return

        print("Inserimento tipi di conto...")
        account_types = [
            AccountType(id=AT_SP_A, tipo_codice="SP-A", nome="Stato Patrimoniale Attivo", posizione_bilancio="Attivo"),
            AccountType(id=AT_SP_P, tipo_codice="SP-P", nome="Stato Patrimoniale Passivo", posizione_bilancio="Passivo"),
            AccountType(id=AT_CE_C, tipo_codice="CE-C", nome="Conto Economico Costi", posizione_bilancio="Costi"),
            AccountType(id=AT_CE_R, tipo_codice="CE-R", nome="Conto Economico Ricavi", posizione_bilancio="Ricavi"),
        ]
        for at in account_types:
            db.add(at)

        print("Inserimento utente admin...")
        admin = User(
            id=ADMIN_ID,
            studio_id=STUDIO_ID,
            email=settings.SEED_ADMIN_EMAIL,
            hashed_password=hash_password(settings.SEED_ADMIN_PASSWORD),
            full_name="Admin Studio Rossi",
            is_active=True,
            role="admin",
        )
        db.add(admin)

        print("Inserimento aziende clienti...")
        meloni = ClientEntity(
            id=CLIENT_MELONI_ID,
            studio_id=STUDIO_ID,
            ragione_sociale="Impianti Meloni S.r.l.",
            codice_fiscale="MLNCRL80A01H501Z",
            partita_iva="01234567890",
            fiscal_regime="ordinario",
            periodicita_iva="mensile",
            is_active=True,
            created_by=ADMIN_ID,
            updated_by=ADMIN_ID,
        )
        pilia = ClientEntity(
            id=CLIENT_PILIA_ID,
            studio_id=STUDIO_ID,
            ragione_sociale="Studio Grafico Pilia",
            codice_fiscale="PLIGNN75B02L219Z",
            partita_iva="09876543210",
            fiscal_regime="semplificato",
            periodicita_iva="trimestrale",
            is_active=True,
            created_by=ADMIN_ID,
            updated_by=ADMIN_ID,
        )
        mura = ClientEntity(
            id=CLIENT_MURA_ID,
            studio_id=STUDIO_ID,
            ragione_sociale="Artigiano Mura",
            codice_fiscale="MRUGNN70C03C352Z",
            partita_iva=None,
            fiscal_regime="forfettario",
            periodicita_iva=None,
            is_active=True,
            created_by=ADMIN_ID,
            updated_by=ADMIN_ID,
        )
        for c in [meloni, pilia, mura]:
            db.add(c)

        print("Inserimento esercizi fiscali...")
        fiscal_years = [
            FiscalYear(
                id=uuid.uuid4(), studio_id=STUDIO_ID, client_entity_id=CLIENT_MELONI_ID,
                anno=2024, data_inizio=date(2024, 1, 1), data_fine=date(2024, 12, 31),
                stato="chiuso", created_by=ADMIN_ID,
            ),
            FiscalYear(
                id=uuid.uuid4(), studio_id=STUDIO_ID, client_entity_id=CLIENT_MELONI_ID,
                anno=2025, data_inizio=date(2025, 1, 1), data_fine=date(2025, 12, 31),
                stato="aperto", created_by=ADMIN_ID,
            ),
            FiscalYear(
                id=uuid.uuid4(), studio_id=STUDIO_ID, client_entity_id=CLIENT_PILIA_ID,
                anno=2025, data_inizio=date(2025, 1, 1), data_fine=date(2025, 12, 31),
                stato="aperto", created_by=ADMIN_ID,
            ),
            FiscalYear(
                id=uuid.uuid4(), studio_id=STUDIO_ID, client_entity_id=CLIENT_MURA_ID,
                anno=2025, data_inizio=date(2025, 1, 1), data_fine=date(2025, 12, 31),
                stato="aperto", created_by=ADMIN_ID,
            ),
        ]
        for fy in fiscal_years:
            db.add(fy)

        await db.flush()

        print("Inserimento piano dei conti standard per Impianti Meloni S.r.l....")
        plan = AccountPlan(
            id=PLAN_MELONI_ID,
            studio_id=STUDIO_ID,
            client_entity_id=CLIENT_MELONI_ID,
            nome="Piano dei Conti Standard Italiano",
            is_default=True,
        )
        db.add(plan)
        await db.flush()

        # Mappa codice → ID per i parent
        codice_to_id: dict[str, uuid.UUID] = {}

        for at_id, codice, nome, livello, parent_codice in PIANO_CONTI:
            account_id = uuid.uuid4()
            codice_to_id[codice] = account_id
            parent_id = codice_to_id.get(parent_codice) if parent_codice else None
            account = Account(
                id=account_id,
                studio_id=STUDIO_ID,
                account_plan_id=PLAN_MELONI_ID,
                account_type_id=at_id,
                codice=codice,
                nome=nome,
                livello=livello,
                parent_id=parent_id,
                is_active=True,
            )
            db.add(account)

        await db.commit()
        print("Seed completato con successo!")
        print(f"Admin: {settings.SEED_ADMIN_EMAIL} / {settings.SEED_ADMIN_PASSWORD}")
        print(f"Clienti inseriti: Impianti Meloni S.r.l., Studio Grafico Pilia, Artigiano Mura")


if __name__ == "__main__":
    asyncio.run(main())
