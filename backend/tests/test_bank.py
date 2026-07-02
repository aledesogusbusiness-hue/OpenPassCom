"""
Test Phase 6 — Riconciliazione bancaria.

Fixtures:
- setup_bank: cliente base per i test banca
"""
import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


# ── Fixture base ──────────────────────────────────────────────────────────────

@pytest_asyncio.fixture()
async def setup_bank(client: AsyncClient, auth_headers: dict):
    """Crea un cliente base per i test banca."""
    resp = await client.post(
        "/api/v1/clients",
        json={
            "ragione_sociale": "Banca Test S.r.l.",
            "fiscal_regime": "ordinario",
            "periodicita_iva": "mensile",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    client_id = uuid.UUID(resp.json()["id"])
    return {"client_id": client_id}


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _create_statement(
    client: AsyncClient,
    auth_headers: dict,
    client_id: uuid.UUID,
    iban: str = "IT60X0542811101000000123456",
) -> dict:
    resp = await client.post(
        f"/api/v1/clients/{client_id}/bank-statements",
        json={
            "iban": iban,
            "data_inizio": "2024-01-01",
            "data_fine": "2024-01-31",
            "saldo_iniziale": "1000.00",
            "saldo_finale": "1500.00",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _create_tx(
    client: AsyncClient,
    auth_headers: dict,
    client_id: uuid.UUID,
    stmt_id: str,
    importo: str = "100.00",
    tipo: str = "entrata",
    data: str = "2024-01-15",
) -> dict:
    resp = await client.post(
        f"/api/v1/clients/{client_id}/bank-statements/{stmt_id}/transactions",
        json=[{
            "data_valuta": data,
            "data_contabile": data,
            "descrizione": f"Transazione {tipo}",
            "importo": importo,
            "tipo": tipo,
        }],
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()[0]


# ── Test ──────────────────────────────────────────────────────────────────────

async def test_create_bank_statement(
    client: AsyncClient, auth_headers: dict, setup_bank: dict
):
    """Verifica creazione estratto conto."""
    client_id = setup_bank["client_id"]
    stmt = await _create_statement(client, auth_headers, client_id)

    assert stmt["iban"] == "IT60X0542811101000000123456"
    assert stmt["client_entity_id"] == str(client_id)
    assert "id" in stmt
    assert stmt["saldo_iniziale"] == "1000.00"
    assert stmt["saldo_finale"] == "1500.00"


async def test_import_transactions(
    client: AsyncClient, auth_headers: dict, setup_bank: dict
):
    """Verifica import batch di transazioni."""
    client_id = setup_bank["client_id"]
    stmt = await _create_statement(
        client, auth_headers, client_id, iban="IT60X0542811101000000654321"
    )
    stmt_id = stmt["id"]

    resp = await client.post(
        f"/api/v1/clients/{client_id}/bank-statements/{stmt_id}/transactions",
        json=[
            {
                "data_valuta": "2024-01-05",
                "data_contabile": "2024-01-05",
                "descrizione": "Bonifico in entrata",
                "importo": "500.00",
                "tipo": "entrata",
            },
            {
                "data_valuta": "2024-01-10",
                "data_contabile": "2024-01-10",
                "descrizione": "Pagamento fornitore",
                "importo": "150.00",
                "tipo": "uscita",
            },
        ],
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert len(data) == 2
    assert all(tx["stato_riconciliazione"] == "da_riconciliare" for tx in data)
    assert all(tx["bank_statement_id"] == stmt_id for tx in data)


async def test_reconcile_with_journal_entry(
    client: AsyncClient, auth_headers: dict, setup_bank: dict
):
    """Verifica riconciliazione con journal entry."""
    client_id = setup_bank["client_id"]
    stmt = await _create_statement(
        client, auth_headers, client_id, iban="IT60X0542811101000000111111"
    )
    stmt_id = stmt["id"]
    tx = await _create_tx(client, auth_headers, client_id, stmt_id)
    tx_id = tx["id"]

    journal_entry_id = str(uuid.uuid4())
    resp = await client.post(
        f"/api/v1/clients/{client_id}/bank-statements/{stmt_id}/transactions/{tx_id}/reconcile",
        json={"journal_entry_id": journal_entry_id},
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["stato_riconciliazione"] == "riconciliata"
    assert data["journal_entry_id"] == journal_entry_id


async def test_reconcile_with_payment(
    client: AsyncClient, auth_headers: dict, setup_bank: dict
):
    """Verifica riconciliazione con scheduled payment."""
    client_id = setup_bank["client_id"]
    stmt = await _create_statement(
        client, auth_headers, client_id, iban="IT60X0542811101000000222222"
    )
    stmt_id = stmt["id"]
    tx = await _create_tx(
        client, auth_headers, client_id, stmt_id,
        importo="200.00", tipo="uscita", data="2024-01-20"
    )
    tx_id = tx["id"]

    scheduled_payment_id = str(uuid.uuid4())
    resp = await client.post(
        f"/api/v1/clients/{client_id}/bank-statements/{stmt_id}/transactions/{tx_id}/reconcile",
        json={"scheduled_payment_id": scheduled_payment_id},
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["stato_riconciliazione"] == "riconciliata"
    assert data["scheduled_payment_id"] == scheduled_payment_id


async def test_mark_irrilevante(
    client: AsyncClient, auth_headers: dict, setup_bank: dict
):
    """Verifica transizione a stato irrilevante."""
    client_id = setup_bank["client_id"]
    stmt = await _create_statement(
        client, auth_headers, client_id, iban="IT60X0542811101000000333333"
    )
    stmt_id = stmt["id"]
    tx = await _create_tx(
        client, auth_headers, client_id, stmt_id,
        importo="5.00", tipo="uscita", data="2024-01-25"
    )
    tx_id = tx["id"]

    resp = await client.post(
        f"/api/v1/clients/{client_id}/bank-statements/{stmt_id}/transactions/{tx_id}/mark-irrilevante",
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["stato_riconciliazione"] == "irrilevante"


async def test_reconciliation_summary(
    client: AsyncClient, auth_headers: dict, setup_bank: dict
):
    """Verifica il summary della riconciliazione."""
    client_id = setup_bank["client_id"]
    stmt = await _create_statement(
        client, auth_headers, client_id, iban="IT60X0542811101000000444444"
    )
    stmt_id = stmt["id"]

    # Importa 3 transazioni
    resp = await client.post(
        f"/api/v1/clients/{client_id}/bank-statements/{stmt_id}/transactions",
        json=[
            {
                "data_valuta": "2024-01-01",
                "data_contabile": "2024-01-01",
                "descrizione": "Tx1",
                "importo": "100.00",
                "tipo": "entrata",
            },
            {
                "data_valuta": "2024-01-02",
                "data_contabile": "2024-01-02",
                "descrizione": "Tx2",
                "importo": "50.00",
                "tipo": "uscita",
            },
            {
                "data_valuta": "2024-01-03",
                "data_contabile": "2024-01-03",
                "descrizione": "Tx3",
                "importo": "200.00",
                "tipo": "entrata",
            },
        ],
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    txs = resp.json()
    tx1_id = txs[0]["id"]
    tx3_id = txs[2]["id"]

    # Riconcilia tx1 con journal entry
    je_id = str(uuid.uuid4())
    await client.post(
        f"/api/v1/clients/{client_id}/bank-statements/{stmt_id}/transactions/{tx1_id}/reconcile",
        json={"journal_entry_id": je_id},
        headers=auth_headers,
    )

    # Marca tx3 irrilevante
    await client.post(
        f"/api/v1/clients/{client_id}/bank-statements/{stmt_id}/transactions/{tx3_id}/mark-irrilevante",
        headers=auth_headers,
    )

    # Ottieni summary
    resp = await client.get(
        f"/api/v1/clients/{client_id}/bank-statements/{stmt_id}/summary",
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["totale"] == 3
    assert data["riconciliate"] == 1
    assert data["da_riconciliare"] == 1
    assert data["irrilevanti"] == 1
    # saldo_riconciliato = importo di tx1 (100.00)
    assert float(data["saldo_riconciliato"]) == 100.0
