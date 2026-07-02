"""
Test Phase 3 — Import e parsing FatturaPA XML.
"""
import uuid
from decimal import Decimal

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.accounting import AccountPlan, Account
from app.services.fattura_pa_service import parse_fattura_pa

pytestmark = pytest.mark.asyncio

STUDIO_ID = uuid.UUID(settings.STUDIO_ID)
AT_SP_A_ID = uuid.UUID("10000000-0000-0000-0000-000000000001")
AT_SP_P_ID = uuid.UUID("10000000-0000-0000-0000-000000000002")
AT_CE_C_ID = uuid.UUID("10000000-0000-0000-0000-000000000003")

# ── XML di test ───────────────────────────────────────────────────────────────

FATTURA_PA_XML_VALIDA = '''<?xml version="1.0" encoding="UTF-8"?>
<FatturaElettronica versione="FPR12" xmlns="http://ivaservizi.agenziaentrate.gov.it/docs/xsd/fatture/v1.2">
  <FatturaElettronicaHeader>
    <CedentePrestatore>
      <DatiAnagrafici>
        <Anagrafica><Denominazione>Fornitore Test SRL</Denominazione></Anagrafica>
      </DatiAnagrafici>
    </CedentePrestatore>
  </FatturaElettronicaHeader>
  <FatturaElettronicaBody>
    <DatiGenerali>
      <DatiGeneraliDocumento>
        <Numero>2024/001</Numero>
        <Data>2024-03-15</Data>
        <ImportoTotaleDocumento>1220.00</ImportoTotaleDocumento>
      </DatiGeneraliDocumento>
    </DatiGenerali>
    <DatiBeniServizi>
      <DatiRiepilogo>
        <ImponibileImporto>1000.00</ImponibileImporto>
        <Imposta>220.00</Imposta>
      </DatiRiepilogo>
    </DatiBeniServizi>
  </FatturaElettronicaBody>
</FatturaElettronica>'''

FATTURA_PA_XML_NO_NS = '''<?xml version="1.0" encoding="UTF-8"?>
<FatturaElettronica versione="FPR12">
  <FatturaElettronicaHeader>
    <CedentePrestatore>
      <DatiAnagrafici>
        <Anagrafica><Denominazione>Fornitore Senza NS</Denominazione></Anagrafica>
      </DatiAnagrafici>
    </CedentePrestatore>
  </FatturaElettronicaHeader>
  <FatturaElettronicaBody>
    <DatiGenerali>
      <DatiGeneraliDocumento>
        <Numero>2024/002</Numero>
        <Data>2024-03-20</Data>
        <ImportoTotaleDocumento>610.00</ImportoTotaleDocumento>
      </DatiGeneraliDocumento>
    </DatiGenerali>
    <DatiBeniServizi>
      <DatiRiepilogo>
        <ImponibileImporto>500.00</ImponibileImporto>
        <Imposta>110.00</Imposta>
      </DatiRiepilogo>
    </DatiBeniServizi>
  </FatturaElettronicaBody>
</FatturaElettronica>'''

FATTURA_PA_XML_INVALIDA = "<?xml version='1.0'?><rotto non chiuso>"


# ── Fixture base ──────────────────────────────────────────────────────────────

@pytest_asyncio.fixture()
async def setup_fpa(client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
    """Cliente + esercizio + conti per test FatturaPA."""
    resp = await client.post("/api/v1/clients", json={
        "ragione_sociale": "Studio FatturaPA SRL",
        "fiscal_regime": "ordinario",
        "periodicita_iva": "mensile",
    }, headers=auth_headers)
    assert resp.status_code == 201, resp.text
    client_id = uuid.UUID(resp.json()["id"])

    fy_resp = await client.post(
        f"/api/v1/clients/{client_id}/fiscal-years",
        json={"anno": 2024, "data_inizio": "2024-01-01", "data_fine": "2024-12-31"},
        headers=auth_headers,
    )
    assert fy_resp.status_code == 201
    fy_id = uuid.UUID(fy_resp.json()["id"])

    # Conti per elaborate
    plan_id = uuid.uuid4()
    fornitore_id = uuid.uuid4()
    iva_id = uuid.uuid4()
    debito_id = uuid.uuid4()

    db_session.add(AccountPlan(
        id=plan_id, studio_id=STUDIO_ID, client_entity_id=client_id,
        nome="Piano FPA Test", is_default=True,
    ))
    db_session.add(Account(
        id=fornitore_id, studio_id=STUDIO_ID, account_plan_id=plan_id,
        account_type_id=AT_CE_C_ID, codice="6001", nome="Costi fornitore", livello=1,
    ))
    db_session.add(Account(
        id=iva_id, studio_id=STUDIO_ID, account_plan_id=plan_id,
        account_type_id=AT_SP_A_ID, codice="1601", nome="IVA a credito", livello=1,
    ))
    db_session.add(Account(
        id=debito_id, studio_id=STUDIO_ID, account_plan_id=plan_id,
        account_type_id=AT_SP_P_ID, codice="2101", nome="Debiti fornitori", livello=1,
    ))
    await db_session.flush()

    return {
        "client_id": str(client_id),
        "fy_id": str(fy_id),
        "account_id_fornitore": str(fornitore_id),
        "account_id_iva": str(iva_id),
        "account_id_debito": str(debito_id),
    }


# ── Test 1: parsing XML valido ────────────────────────────────────────────────

async def test_parse_valid_xml() -> None:
    """Parse FatturaPA XML con namespace estrae i dati correttamente."""
    result = parse_fattura_pa(FATTURA_PA_XML_VALIDA)

    assert result["cedente_prestatore"] == "Fornitore Test SRL"
    assert result["numero_fattura"] == "2024/001"
    assert result["data_fattura"] == "2024-03-15"
    assert Decimal(result["imponibile_totale"]) == Decimal("1000.00")
    assert Decimal(result["iva_totale"]) == Decimal("220.00")
    assert Decimal(result["totale_documento"]) == Decimal("1220.00")


async def test_parse_valid_xml_no_namespace() -> None:
    """Parse FatturaPA XML senza namespace estrae i dati correttamente."""
    result = parse_fattura_pa(FATTURA_PA_XML_NO_NS)

    assert result["cedente_prestatore"] == "Fornitore Senza NS"
    assert result["numero_fattura"] == "2024/002"
    assert Decimal(result["imponibile_totale"]) == Decimal("500.00")
    assert Decimal(result["iva_totale"]) == Decimal("110.00")


# ── Test 2: XML malformato → stato='errore' ───────────────────────────────────

async def test_parse_invalid_xml(
    client: AsyncClient, auth_headers: dict, setup_fpa: dict
) -> None:
    """XML malformato → FatturaPAImport con stato='errore'."""
    d = setup_fpa
    url = f"/api/v1/clients/{d['client_id']}/fiscal-years/{d['fy_id']}/fatture-pa/import"

    resp = await client.post(url, json={
        "filename": "errore.xml",
        "xml_content": FATTURA_PA_XML_INVALIDA,
    }, headers=auth_headers)

    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["stato"] == "errore"
    assert body["errore_msg"] is not None
    assert len(body["errore_msg"]) > 0


# ── Test 3: import fattura valida ─────────────────────────────────────────────

async def test_import_fattura(
    client: AsyncClient, auth_headers: dict, setup_fpa: dict
) -> None:
    """Import fattura valida → stato='importata' con parsed_data."""
    d = setup_fpa
    url = f"/api/v1/clients/{d['client_id']}/fiscal-years/{d['fy_id']}/fatture-pa/import"

    resp = await client.post(url, json={
        "filename": "IT01234567890_FPR01.xml",
        "xml_content": FATTURA_PA_XML_VALIDA,
    }, headers=auth_headers)

    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["stato"] == "importata"
    assert body["filename"] == "IT01234567890_FPR01.xml"
    assert body["parsed_data"] is not None
    assert body["parsed_data"]["cedente_prestatore"] == "Fornitore Test SRL"
    assert body["parsed_data"]["numero_fattura"] == "2024/001"
    assert body["journal_entry_id"] is None
    assert body["errore_msg"] is None

    # Verifica che appaia nella lista
    resp_list = await client.get(
        f"/api/v1/clients/{d['client_id']}/fiscal-years/{d['fy_id']}/fatture-pa",
        headers=auth_headers,
    )
    assert resp_list.status_code == 200
    assert len(resp_list.json()) >= 1

    # Dettaglio
    import_id = body["id"]
    resp_detail = await client.get(
        f"/api/v1/clients/{d['client_id']}/fiscal-years/{d['fy_id']}/fatture-pa/{import_id}",
        headers=auth_headers,
    )
    assert resp_detail.status_code == 200
    assert resp_detail.json()["id"] == import_id


# ── Test 4: elaborate fattura → crea JournalEntry bozza ──────────────────────

async def test_elaborate_fattura(
    client: AsyncClient, auth_headers: dict, setup_fpa: dict
) -> None:
    """Elaborazione fattura crea JournalEntry draft con le righe corrette."""
    d = setup_fpa
    base_url = f"/api/v1/clients/{d['client_id']}/fiscal-years/{d['fy_id']}/fatture-pa"

    # Importa fattura
    resp_import = await client.post(f"{base_url}/import", json={
        "filename": "IT01234567890_FPR02.xml",
        "xml_content": FATTURA_PA_XML_VALIDA,
    }, headers=auth_headers)
    assert resp_import.status_code == 201
    import_id = resp_import.json()["id"]

    # Elabora
    resp = await client.post(
        f"{base_url}/{import_id}/elaborate",
        json={
            "account_id_fornitore": d["account_id_fornitore"],
            "account_id_iva": d["account_id_iva"],
            "account_id_debito": d["account_id_debito"],
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()

    # Import aggiornato
    assert body["import"]["stato"] == "elaborata"
    assert body["import"]["journal_entry_id"] is not None

    # JournalEntry creata in stato draft
    assert body["journal_entry"]["stato"] == "draft"
    assert body["journal_entry"]["causale"] == "FA"

    # Elaborazione seconda volta → errore
    resp2 = await client.post(
        f"{base_url}/{import_id}/elaborate",
        json={
            "account_id_fornitore": d["account_id_fornitore"],
            "account_id_iva": d["account_id_iva"],
            "account_id_debito": d["account_id_debito"],
        },
        headers=auth_headers,
    )
    assert resp2.status_code == 422
