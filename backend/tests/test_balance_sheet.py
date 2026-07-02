"""
Test Phase 4 — Stato Patrimoniale, Conto Economico, Chiusura esercizio.

Fixtures:
- setup_bs: cliente + esercizio 2024 + piano dei conti con 4 conti
  (SP-A, SP-P, CE-C, CE-R) inseriti direttamente in db_session.
"""
import uuid
from decimal import Decimal

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.accounting import AccountPlan, Account

pytestmark = pytest.mark.asyncio

STUDIO_ID = uuid.UUID(settings.STUDIO_ID)

# ID AccountType fissati dal seed in conftest.py
AT_SP_A = uuid.UUID("10000000-0000-0000-0000-000000000001")
AT_SP_P = uuid.UUID("10000000-0000-0000-0000-000000000002")
AT_CE_C = uuid.UUID("10000000-0000-0000-0000-000000000003")
AT_CE_R = uuid.UUID("10000000-0000-0000-0000-000000000004")


# ── Fixture base ─────────────────────────────────────────────────────────────

@pytest_asyncio.fixture()
async def setup_bs(client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
    """
    Prepara:
    - cliente ordinario (via API)
    - esercizio 2024 (via API)
    - piano dei conti + 4 conti (SP-A, SP-P, CE-C, CE-R) via db_session
    """
    resp = await client.post(
        "/api/v1/clients",
        json={
            "ragione_sociale": "Test Bilancio S.r.l.",
            "fiscal_regime": "ordinario",
            "periodicita_iva": "mensile",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    client_id = uuid.UUID(resp.json()["id"])

    fy_resp = await client.post(
        f"/api/v1/clients/{client_id}/fiscal-years",
        json={"anno": 2024, "data_inizio": "2024-01-01", "data_fine": "2024-12-31"},
        headers=auth_headers,
    )
    assert fy_resp.status_code == 201, fy_resp.text
    fy_id = uuid.UUID(fy_resp.json()["id"])

    # Piano dei conti + conti direttamente in db_session
    plan_id = uuid.uuid4()
    db_session.add(AccountPlan(
        id=plan_id,
        studio_id=STUDIO_ID,
        client_entity_id=client_id,
        nome="Piano BS Test",
        is_default=True,
    ))

    cassa_id = uuid.uuid4()
    capitale_id = uuid.uuid4()
    costi_id = uuid.uuid4()
    ricavi_id = uuid.uuid4()

    db_session.add(Account(
        id=cassa_id, studio_id=STUDIO_ID, account_plan_id=plan_id,
        account_type_id=AT_SP_A, codice="1001", nome="Cassa", livello=1,
    ))
    db_session.add(Account(
        id=capitale_id, studio_id=STUDIO_ID, account_plan_id=plan_id,
        account_type_id=AT_SP_P, codice="2001", nome="Capitale Sociale", livello=1,
    ))
    db_session.add(Account(
        id=costi_id, studio_id=STUDIO_ID, account_plan_id=plan_id,
        account_type_id=AT_CE_C, codice="3001", nome="Costi Servizi", livello=1,
    ))
    db_session.add(Account(
        id=ricavi_id, studio_id=STUDIO_ID, account_plan_id=plan_id,
        account_type_id=AT_CE_R, codice="4001", nome="Ricavi Vendite", livello=1,
    ))
    await db_session.flush()

    return {
        "client_id": str(client_id),
        "fy_id": str(fy_id),
        "cassa_id": str(cassa_id),
        "capitale_id": str(capitale_id),
        "costi_id": str(costi_id),
        "ricavi_id": str(ricavi_id),
    }


async def _post_entry(client: AsyncClient, auth_headers: dict, client_id: str,
                      fy_id: str, dare_account: str, avere_account: str,
                      importo: str) -> dict:
    """Helper: crea e posta una scrittura a partita doppia bilanciata."""
    entry_resp = await client.post(
        f"/api/v1/clients/{client_id}/fiscal-years/{fy_id}/journal-entries",
        json={
            "data_registrazione": "2024-06-30",
            "descrizione": "Scrittura test",
            "causale": "PN",
            "lines": [
                {"account_id": dare_account, "dare": importo, "avere": "0"},
                {"account_id": avere_account, "dare": "0", "avere": importo},
            ],
        },
        headers=auth_headers,
    )
    assert entry_resp.status_code == 201, entry_resp.text
    entry_id = entry_resp.json()["id"]

    post_resp = await client.post(
        f"/api/v1/clients/{client_id}/fiscal-years/{fy_id}/journal-entries/{entry_id}/post",
        headers=auth_headers,
    )
    assert post_resp.status_code == 200, post_resp.text
    return post_resp.json()


# ── Stato Patrimoniale ────────────────────────────────────────────────────────

async def test_stato_patrimoniale_empty(
    client: AsyncClient, auth_headers: dict, setup_bs: dict
):
    """Senza movimenti → SP con totali zero e quadrato=True."""
    cid, yid = setup_bs["client_id"], setup_bs["fy_id"]

    resp = await client.get(
        f"/api/v1/clients/{cid}/fiscal-years/{yid}/stato-patrimoniale",
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["totale_attivo"] == "0"
    assert data["totale_passivo"] == "0"
    assert data["quadrato"] is True
    assert data["attivo"]["voci"] == []
    assert data["passivo"]["voci"] == []


async def test_stato_patrimoniale_with_entries(
    client: AsyncClient, auth_headers: dict, setup_bs: dict
):
    """
    Con JournalEntry postata: Cassa (SP-A) a Capitale (SP-P) 10000
    → attivo = 10000, passivo = 10000, quadrato = True.
    """
    cid, yid = setup_bs["client_id"], setup_bs["fy_id"]
    cassa_id = setup_bs["cassa_id"]
    capitale_id = setup_bs["capitale_id"]

    await _post_entry(client, auth_headers, cid, yid, cassa_id, capitale_id, "10000.00")

    resp = await client.get(
        f"/api/v1/clients/{cid}/fiscal-years/{yid}/stato-patrimoniale",
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert Decimal(data["totale_attivo"]) == Decimal("10000.00")
    assert Decimal(data["totale_passivo"]) == Decimal("10000.00")
    assert data["quadrato"] is True

    # Verifica voci
    attivo_codici = [v["codice"] for v in data["attivo"]["voci"]]
    assert "1001" in attivo_codici  # Cassa
    passivo_codici = [v["codice"] for v in data["passivo"]["voci"]]
    assert "2001" in passivo_codici  # Capitale Sociale


# ── Conto Economico ───────────────────────────────────────────────────────────

async def test_conto_economico_empty(
    client: AsyncClient, auth_headers: dict, setup_bs: dict
):
    """Senza movimenti → CE con totali zero."""
    cid, yid = setup_bs["client_id"], setup_bs["fy_id"]

    resp = await client.get(
        f"/api/v1/clients/{cid}/fiscal-years/{yid}/conto-economico",
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["ricavi"]["voci"] == []
    assert data["costi"]["voci"] == []
    assert data["risultato_operativo"] == "0"
    assert data["utile_perdita"] == "0"


async def test_conto_economico_with_entries(
    client: AsyncClient, auth_headers: dict, setup_bs: dict
):
    """
    Con JournalEntry:
    - Cassa (SP-A) a Ricavi (CE-R) 5000 → ricavi = 5000
    - Costi (CE-C) a Cassa (SP-A) 3000  → costi = 3000
    - risultato_operativo = 5000 - 3000 = 2000
    """
    cid, yid = setup_bs["client_id"], setup_bs["fy_id"]
    cassa_id = setup_bs["cassa_id"]
    ricavi_id = setup_bs["ricavi_id"]
    costi_id = setup_bs["costi_id"]

    # Vendita: Cassa a Ricavi 5000
    await _post_entry(client, auth_headers, cid, yid, cassa_id, ricavi_id, "5000.00")
    # Costo: Costi a Cassa 3000
    await _post_entry(client, auth_headers, cid, yid, costi_id, cassa_id, "3000.00")

    resp = await client.get(
        f"/api/v1/clients/{cid}/fiscal-years/{yid}/conto-economico",
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert Decimal(data["ricavi"]["totale"]) == Decimal("5000.00")
    assert Decimal(data["costi"]["totale"]) == Decimal("3000.00")
    assert Decimal(data["risultato_operativo"]) == Decimal("2000.00")
    assert Decimal(data["utile_perdita"]) == Decimal("2000.00")

    ricavi_codici = [v["codice"] for v in data["ricavi"]["voci"]]
    assert "4001" in ricavi_codici
    costi_codici = [v["codice"] for v in data["costi"]["voci"]]
    assert "3001" in costi_codici


# ── Chiusura esercizio ────────────────────────────────────────────────────────

async def test_close_fiscal_year(
    client: AsyncClient, auth_headers: dict, setup_bs: dict
):
    """
    Chiude l'esercizio → crea YearClosing con stato='chiuso',
    FiscalYear diventa 'chiuso'.
    """
    cid, yid = setup_bs["client_id"], setup_bs["fy_id"]

    close_resp = await client.post(
        f"/api/v1/clients/{cid}/fiscal-years/{yid}/close",
        json={"note": "Chiusura test"},
        headers=auth_headers,
    )
    assert close_resp.status_code == 200, close_resp.text
    closing = close_resp.json()

    assert closing["stato"] == "chiuso"
    assert closing["fiscal_year_id"] == yid
    assert closing["data_chiusura"] is not None
    assert closing["note"] == "Chiusura test"

    # Verifica che FiscalYear sia chiuso
    fy_resp = await client.get(
        f"/api/v1/clients/{cid}/fiscal-years",
        headers=auth_headers,
    )
    assert fy_resp.status_code == 200
    years = fy_resp.json()
    fy = next((y for y in years if y["id"] == yid), None)
    assert fy is not None
    assert fy["stato"] == "chiuso"

    # Verifica endpoint GET closing
    get_closing = await client.get(
        f"/api/v1/clients/{cid}/fiscal-years/{yid}/closing",
        headers=auth_headers,
    )
    assert get_closing.status_code == 200
    assert get_closing.json()["stato"] == "chiuso"


async def test_close_already_closed(
    client: AsyncClient, auth_headers: dict, setup_bs: dict
):
    """Tentativo di chiudere un esercizio già chiuso → 409."""
    cid, yid = setup_bs["client_id"], setup_bs["fy_id"]

    # Prima chiusura
    r1 = await client.post(
        f"/api/v1/clients/{cid}/fiscal-years/{yid}/close",
        headers=auth_headers,
    )
    assert r1.status_code == 200, r1.text

    # Seconda chiusura → 409
    r2 = await client.post(
        f"/api/v1/clients/{cid}/fiscal-years/{yid}/close",
        headers=auth_headers,
    )
    assert r2.status_code == 409
    assert "già chiuso" in r2.json()["detail"]
