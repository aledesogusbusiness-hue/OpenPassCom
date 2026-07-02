"""
Test Phase 2 — Prima nota contabile.

Fixtures:
- setup_journal: crea cliente ordinario, esercizio 2024, piano dei conti, 2 conti.
  Usa la stessa db_session del client fixture → dati visibili alla HTTP app.
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
AT_SP_A_ID = uuid.UUID("10000000-0000-0000-0000-000000000001")
AT_CE_R_ID = uuid.UUID("10000000-0000-0000-0000-000000000004")

# ── Fixture base ─────────────────────────────────────────────────────────────

@pytest_asyncio.fixture()
async def setup_journal(client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
    """
    Prepara: cliente ordinario + esercizio 2024 (via API) +
             piano dei conti e 2 conti (diretti in db_session, stessa sessione).
    """
    # Cliente ordinario
    resp = await client.post("/api/v1/clients", json={
        "ragione_sociale": "Azienda Test Journal S.r.l.",
        "fiscal_regime": "ordinario",
        "periodicita_iva": "mensile",
    }, headers=auth_headers)
    assert resp.status_code == 201, resp.text
    cdata = resp.json()
    client_id = uuid.UUID(cdata["id"])

    # Esercizio 2024
    fy_resp = await client.post(
        f"/api/v1/clients/{client_id}/fiscal-years",
        json={"anno": 2024, "data_inizio": "2024-01-01", "data_fine": "2024-12-31"},
        headers=auth_headers,
    )
    assert fy_resp.status_code == 201, fy_resp.text
    fy_id = uuid.UUID(fy_resp.json()["id"])

    # Piano dei conti + conti (diretti — nessun endpoint POST per account_plan)
    plan_id = uuid.uuid4()
    db_session.add(AccountPlan(
        id=plan_id, studio_id=STUDIO_ID, client_entity_id=client_id,
        nome="Piano Test", is_default=True,
    ))

    cassa_id = uuid.uuid4()
    ricavi_id = uuid.uuid4()
    db_session.add(Account(
        id=cassa_id, studio_id=STUDIO_ID, account_plan_id=plan_id,
        account_type_id=AT_SP_A_ID, codice="1001", nome="Cassa", livello=1,
    ))
    db_session.add(Account(
        id=ricavi_id, studio_id=STUDIO_ID, account_plan_id=plan_id,
        account_type_id=AT_CE_R_ID, codice="4001", nome="Ricavi Vendite", livello=1,
    ))
    await db_session.flush()

    return {
        "client_id": str(client_id),
        "fy_id": str(fy_id),
        "cassa_id": str(cassa_id),
        "ricavi_id": str(ricavi_id),
    }


# ── Helper ───────────────────────────────────────────────────────────────────

def _base_url(client_id: str, fy_id: str) -> str:
    return f"/api/v1/clients/{client_id}/fiscal-years/{fy_id}/journal-entries"


def _make_entry_payload(cassa_id: str, ricavi_id: str, dare: str = "100.00") -> dict:
    return {
        "data_registrazione": "2024-01-15",
        "descrizione": "Incasso cliente Rossi",
        "causale": "FV",
        "lines": [
            {"account_id": cassa_id, "dare": dare, "avere": "0.00"},
            {"account_id": ricavi_id, "dare": "0.00", "avere": dare},
        ],
    }


async def _create_and_post(
    client: AsyncClient, auth_headers: dict, data: dict,
    client_id: str, fy_id: str
) -> dict:
    """Crea un'entry draft e la porta in posted."""
    url = _base_url(client_id, fy_id)
    create = await client.post(url, json=data, headers=auth_headers)
    assert create.status_code == 201, create.text
    entry = create.json()

    post_resp = await client.post(
        f"{url}/{entry['id']}/post", headers=auth_headers
    )
    assert post_resp.status_code == 200, post_resp.text
    return post_resp.json()


# ── Test 1: crea registrazione draft ─────────────────────────────────────────

async def test_create_draft_entry(client: AsyncClient, auth_headers: dict, setup_journal: dict) -> None:
    """Crea una registrazione → stato='draft', numero_registrazione=1."""
    d = setup_journal
    payload = _make_entry_payload(d["cassa_id"], d["ricavi_id"])

    resp = await client.post(_base_url(d["client_id"], d["fy_id"]), json=payload, headers=auth_headers)

    assert resp.status_code == 201, resp.text
    entry = resp.json()
    assert entry["stato"] == "draft"
    assert entry["causale"] == "FV"
    assert entry["numero_registrazione"] == 1
    assert entry["descrizione"] == "Incasso cliente Rossi"


# ── Test 2: post entry valid ──────────────────────────────────────────────────

async def test_post_entry_valid(client: AsyncClient, auth_headers: dict, setup_journal: dict) -> None:
    """Registrazione bilanciata → posted."""
    d = setup_journal
    payload = _make_entry_payload(d["cassa_id"], d["ricavi_id"])

    create = await client.post(_base_url(d["client_id"], d["fy_id"]), json=payload, headers=auth_headers)
    assert create.status_code == 201
    entry_id = create.json()["id"]

    post_resp = await client.post(
        f"{_base_url(d['client_id'], d['fy_id'])}/{entry_id}/post",
        headers=auth_headers,
    )
    assert post_resp.status_code == 200, post_resp.text
    assert post_resp.json()["stato"] == "posted"


# ── Test 3: post entry unbalanced ─────────────────────────────────────────────

async def test_post_entry_unbalanced(client: AsyncClient, auth_headers: dict, setup_journal: dict) -> None:
    """Dare ≠ Avere → 422 Unprocessable Entity."""
    d = setup_journal
    payload = {
        "data_registrazione": "2024-01-15",
        "descrizione": "Registrazione sbagliata",
        "causale": "FA",
        "lines": [
            {"account_id": d["cassa_id"], "dare": "100.00", "avere": "0.00"},
            {"account_id": d["ricavi_id"], "dare": "0.00", "avere": "50.00"},  # non bilanciato
        ],
    }
    create = await client.post(_base_url(d["client_id"], d["fy_id"]), json=payload, headers=auth_headers)
    assert create.status_code == 201
    entry_id = create.json()["id"]

    post_resp = await client.post(
        f"{_base_url(d['client_id'], d['fy_id'])}/{entry_id}/post",
        headers=auth_headers,
    )
    assert post_resp.status_code == 422
    assert "pareggio" in post_resp.json()["detail"].lower()


# ── Test 4: reverse entry ────────────────────────────────────────────────────

async def test_reverse_entry(client: AsyncClient, auth_headers: dict, setup_journal: dict) -> None:
    """Storno: crea nuova entry con segni invertiti, originale → 'reversed'."""
    d = setup_journal
    payload = _make_entry_payload(d["cassa_id"], d["ricavi_id"])
    posted = await _create_and_post(client, auth_headers, payload, d["client_id"], d["fy_id"])
    original_id = posted["id"]

    url_base = _base_url(d["client_id"], d["fy_id"])
    rev_resp = await client.post(
        f"{url_base}/{original_id}/reverse",
        headers=auth_headers,
    )
    assert rev_resp.status_code == 201, rev_resp.text
    storno = rev_resp.json()
    assert storno["stato"] == "posted"
    assert "Storno" in storno["descrizione"]
    assert storno["numero_registrazione"] == 2  # secondo numero

    # Originale deve essere 'reversed'
    get_orig = await client.get(f"{url_base}/{original_id}", headers=auth_headers)
    assert get_orig.status_code == 200
    orig = get_orig.json()
    assert orig["stato"] == "reversed"
    assert orig["reversed_by"] == storno["id"]


# ── Test 5: cannot post reversed ─────────────────────────────────────────────

async def test_cannot_post_reversed(client: AsyncClient, auth_headers: dict, setup_journal: dict) -> None:
    """Non si può postare una registrazione già 'reversed'."""
    d = setup_journal
    payload = _make_entry_payload(d["cassa_id"], d["ricavi_id"])
    posted = await _create_and_post(client, auth_headers, payload, d["client_id"], d["fy_id"])
    original_id = posted["id"]

    url_base = _base_url(d["client_id"], d["fy_id"])
    # Storna l'entry
    await client.post(f"{url_base}/{original_id}/reverse", headers=auth_headers)

    # Tenta di postare la originale (ora 'reversed') → 422
    post_again = await client.post(f"{url_base}/{original_id}/post", headers=auth_headers)
    assert post_again.status_code == 422


# ── Test 6: libro giornale con filtro causale ─────────────────────────────────

async def test_libro_giornale(client: AsyncClient, auth_headers: dict, setup_journal: dict) -> None:
    """Lista registrazioni posted, con filtro causale."""
    d = setup_journal
    url_base = _base_url(d["client_id"], d["fy_id"])

    # Crea 2 entry con causali diverse
    fv_payload = _make_entry_payload(d["cassa_id"], d["ricavi_id"])
    fa_payload = {**fv_payload, "causale": "FA", "descrizione": "Acquisto fornitore"}

    await _create_and_post(client, auth_headers, fv_payload, d["client_id"], d["fy_id"])
    await _create_and_post(client, auth_headers, fa_payload, d["client_id"], d["fy_id"])

    # Tutte le posted
    all_resp = await client.get(url_base, headers=auth_headers)
    assert all_resp.status_code == 200
    assert len(all_resp.json()) == 2

    # Solo FV
    fv_resp = await client.get(f"{url_base}?causale=FV", headers=auth_headers)
    assert fv_resp.status_code == 200
    entries = fv_resp.json()
    assert len(entries) == 1
    assert entries[0]["causale"] == "FV"


# ── Test 7: mastrino ─────────────────────────────────────────────────────────

async def test_mastrino(client: AsyncClient, auth_headers: dict, setup_journal: dict) -> None:
    """Mastrino cassa: 2 movimenti dare, saldo progressivo corretto."""
    d = setup_journal
    url_base = _base_url(d["client_id"], d["fy_id"])

    # 2 registrazioni: entrambe con dare su cassa
    for desc in ["Prima vendita", "Seconda vendita"]:
        payload = {**_make_entry_payload(d["cassa_id"], d["ricavi_id"]), "descrizione": desc}
        await _create_and_post(client, auth_headers, payload, d["client_id"], d["fy_id"])

    mastrino_resp = await client.get(
        f"/api/v1/clients/{d['client_id']}/fiscal-years/{d['fy_id']}/mastrini/{d['cassa_id']}",
        headers=auth_headers,
    )
    assert mastrino_resp.status_code == 200, mastrino_resp.text
    mast = mastrino_resp.json()

    assert len(mast["movimenti"]) == 2
    assert Decimal(str(mast["tot_dare"])) == Decimal("200.00")
    assert Decimal(str(mast["tot_avere"])) == Decimal("0.00")
    assert Decimal(str(mast["saldo"])) == Decimal("200.00")

    # Saldo progressivo primo movimento
    assert Decimal(str(mast["movimenti"][0]["saldo_progressivo"])) == Decimal("100.00")
    # Saldo progressivo secondo movimento
    assert Decimal(str(mast["movimenti"][1]["saldo_progressivo"])) == Decimal("200.00")


# ── Test 8: bilancio di verifica ──────────────────────────────────────────────

async def test_bilancio_verifica(client: AsyncClient, auth_headers: dict, setup_journal: dict) -> None:
    """Bilancio di verifica: somme per conto, totali bilanciati."""
    d = setup_journal
    payload = _make_entry_payload(d["cassa_id"], d["ricavi_id"], dare="250.00")
    await _create_and_post(client, auth_headers, payload, d["client_id"], d["fy_id"])

    resp = await client.get(
        f"/api/v1/clients/{d['client_id']}/fiscal-years/{d['fy_id']}/bilancio-verifica",
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    voci = resp.json()

    # Deve avere 2 conti (cassa e ricavi)
    assert len(voci) == 2

    totale_dare = sum(Decimal(str(v["tot_dare"])) for v in voci)
    totale_avere = sum(Decimal(str(v["tot_avere"])) for v in voci)
    assert totale_dare == totale_avere  # invariante fondamentale della partita doppia

    # Cassa: dare=250, avere=0
    cassa_voce = next(v for v in voci if str(v["account_id"]) == d["cassa_id"])
    assert Decimal(str(cassa_voce["tot_dare"])) == Decimal("250.00")
    assert Decimal(str(cassa_voce["tot_avere"])) == Decimal("0.00")
