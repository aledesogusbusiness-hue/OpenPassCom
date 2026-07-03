"""
Test Phase 9 — Emissione FatturaPA verso SDI (infrastruttura lato nostro).
"""
import uuid
import xml.etree.ElementTree as ET
from decimal import Decimal

import pytest
import pytest_asyncio
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

_NS = "http://ivaservizi.agenziaentrate.gov.it/docs/xsd/fatture/v1.2"


@pytest_asyncio.fixture()
async def setup_export(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        "/api/v1/clients",
        json={
            "ragione_sociale": "Studio Test Export S.r.l.",
            "codice_fiscale": "12345678901",
            "partita_iva": "12345678901",
            "fiscal_regime": "ordinario",
            "periodicita_iva": "mensile",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    client_id = resp.json()["id"]

    fy_resp = await client.post(
        f"/api/v1/clients/{client_id}/fiscal-years",
        json={"anno": 2024, "data_inizio": "2024-01-01", "data_fine": "2024-12-31"},
        headers=auth_headers,
    )
    assert fy_resp.status_code == 201, fy_resp.text
    fy_id = fy_resp.json()["id"]

    return {"client_id": client_id, "fy_id": fy_id}


def _create_payload(numero: str = "1") -> dict:
    return {
        "tipo_documento": "TD01",
        "numero_fattura": numero,
        "data_fattura": "2024-06-15",
        "cedente_indirizzo": "Via Roma 1",
        "cedente_cap": "20100",
        "cedente_comune": "Milano",
        "cedente_provincia": "MI",
        "destinatario_denominazione": "Cliente Finale S.r.l.",
        "destinatario_partita_iva": "09876543210",
        "destinatario_indirizzo": "Via Napoli 5",
        "destinatario_cap": "80100",
        "destinatario_comune": "Napoli",
        "destinatario_provincia": "NA",
        "destinatario_codice_sdi": "0000000",
        "righe": [
            {
                "descrizione": "Consulenza fiscale gennaio 2024",
                "quantita": "1",
                "prezzo_unitario": "1000.00",
                "aliquota_iva": 22,
            },
            {
                "descrizione": "Spese accessorie",
                "quantita": "2",
                "prezzo_unitario": "50.00",
                "aliquota_iva": 22,
            },
        ],
    }


async def _create_and_generate(client: AsyncClient, auth_headers: dict, setup_export: dict, numero="1"):
    cid, yid = setup_export["client_id"], setup_export["fy_id"]
    create_resp = await client.post(
        f"/api/v1/clients/{cid}/fiscal-years/{yid}/fatture-pa-export",
        json=_create_payload(numero),
        headers=auth_headers,
    )
    assert create_resp.status_code == 201, create_resp.text
    export_id = create_resp.json()["id"]

    gen_resp = await client.post(
        f"/api/v1/clients/{cid}/fiscal-years/{yid}/fatture-pa-export/{export_id}/generate-xml",
        headers=auth_headers,
    )
    assert gen_resp.status_code == 200, gen_resp.text
    return export_id, gen_resp.json()


async def test_create_export_bozza(client: AsyncClient, auth_headers: dict, setup_export: dict):
    cid, yid = setup_export["client_id"], setup_export["fy_id"]
    resp = await client.post(
        f"/api/v1/clients/{cid}/fiscal-years/{yid}/fatture-pa-export",
        json=_create_payload(),
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["stato"] == "bozza"
    assert data["xml_content"] is None if "xml_content" in data else True
    assert len(data["righe"]) == 2


async def test_generate_xml_produces_valid_xml(
    client: AsyncClient, auth_headers: dict, setup_export: dict
):
    cid, yid = setup_export["client_id"], setup_export["fy_id"]
    export_id, data = await _create_and_generate(client, auth_headers, setup_export)

    assert data["stato"] == "generata"
    assert data["progressivo_invio"] is not None

    # Scarica e valida che sia XML ben formato con i dati attesi
    dl_resp = await client.get(
        f"/api/v1/clients/{cid}/fiscal-years/{yid}/fatture-pa-export/{export_id}/download",
        headers=auth_headers,
    )
    assert dl_resp.status_code == 200
    assert dl_resp.headers["content-type"] == "application/xml"

    root = ET.fromstring(dl_resp.content)
    # Solo l'elemento radice porta il namespace p: — i figli sono senza prefisso,
    # come nei file FatturaPA reali.
    assert root.tag == f"{{{_NS}}}FatturaElettronica"

    denominazione = root.find(
        ".//CedentePrestatore/DatiAnagrafici/Anagrafica/Denominazione"
    )
    assert denominazione is not None
    assert denominazione.text == "Studio Test Export S.r.l."

    regime = root.find(".//CedentePrestatore/DatiAnagrafici/RegimeFiscale")
    assert regime.text == "RF01"

    linee = root.findall(".//DettaglioLinee")
    assert len(linee) == 2

    totale = root.find(".//ImportoTotaleDocumento")
    # imponibile: 1000 + 100 = 1100; iva 22% = 242; totale = 1342.00
    assert Decimal(totale.text) == Decimal("1342.00")


async def test_generate_xml_requires_lines(client: AsyncClient, auth_headers: dict, setup_export: dict):
    cid, yid = setup_export["client_id"], setup_export["fy_id"]
    payload = _create_payload()
    payload["righe"] = []
    # Zod/pydantic richiede almeno una riga a livello di schema
    resp = await client.post(
        f"/api/v1/clients/{cid}/fiscal-years/{yid}/fatture-pa-export",
        json=payload,
        headers=auth_headers,
    )
    assert resp.status_code == 422


async def test_progressivo_invio_increments(client: AsyncClient, auth_headers: dict, setup_export: dict):
    _, data1 = await _create_and_generate(client, auth_headers, setup_export, numero="1")
    _, data2 = await _create_and_generate(client, auth_headers, setup_export, numero="2")
    assert data1["progressivo_invio"] != data2["progressivo_invio"]


async def test_download_before_generate_fails(
    client: AsyncClient, auth_headers: dict, setup_export: dict
):
    cid, yid = setup_export["client_id"], setup_export["fy_id"]
    create_resp = await client.post(
        f"/api/v1/clients/{cid}/fiscal-years/{yid}/fatture-pa-export",
        json=_create_payload(),
        headers=auth_headers,
    )
    export_id = create_resp.json()["id"]

    dl_resp = await client.get(
        f"/api/v1/clients/{cid}/fiscal-years/{yid}/fatture-pa-export/{export_id}/download",
        headers=auth_headers,
    )
    assert dl_resp.status_code == 422


async def test_full_lifecycle_inviata_and_esito(
    client: AsyncClient, auth_headers: dict, setup_export: dict
):
    cid, yid = setup_export["client_id"], setup_export["fy_id"]
    export_id, data = await _create_and_generate(client, auth_headers, setup_export)
    assert data["stato"] == "generata"

    inviata_resp = await client.post(
        f"/api/v1/clients/{cid}/fiscal-years/{yid}/fatture-pa-export/{export_id}/mark-inviata",
        json={"identificativo_sdi": "SDI-12345"},
        headers=auth_headers,
    )
    assert inviata_resp.status_code == 200, inviata_resp.text
    inviata_data = inviata_resp.json()
    assert inviata_data["stato"] == "inviata"
    assert inviata_data["identificativo_sdi"] == "SDI-12345"
    assert inviata_data["data_invio"] is not None

    esito_resp = await client.post(
        f"/api/v1/clients/{cid}/fiscal-years/{yid}/fatture-pa-export/{export_id}/mark-esito",
        json={"esito": "accettata", "messaggio": "Ricevuta di consegna"},
        headers=auth_headers,
    )
    assert esito_resp.status_code == 200, esito_resp.text
    esito_data = esito_resp.json()
    assert esito_data["stato"] == "accettata"
    assert esito_data["esito_messaggio"] == "Ricevuta di consegna"
    assert esito_data["data_esito"] is not None


async def test_cannot_mark_inviata_before_generate(
    client: AsyncClient, auth_headers: dict, setup_export: dict
):
    cid, yid = setup_export["client_id"], setup_export["fy_id"]
    create_resp = await client.post(
        f"/api/v1/clients/{cid}/fiscal-years/{yid}/fatture-pa-export",
        json=_create_payload(),
        headers=auth_headers,
    )
    export_id = create_resp.json()["id"]

    resp = await client.post(
        f"/api/v1/clients/{cid}/fiscal-years/{yid}/fatture-pa-export/{export_id}/mark-inviata",
        json={},
        headers=auth_headers,
    )
    assert resp.status_code == 422


async def test_cannot_mark_esito_before_inviata(
    client: AsyncClient, auth_headers: dict, setup_export: dict
):
    cid, yid = setup_export["client_id"], setup_export["fy_id"]
    export_id, _ = await _create_and_generate(client, auth_headers, setup_export)

    resp = await client.post(
        f"/api/v1/clients/{cid}/fiscal-years/{yid}/fatture-pa-export/{export_id}/mark-esito",
        json={"esito": "accettata"},
        headers=auth_headers,
    )
    assert resp.status_code == 422


async def test_list_exports(client: AsyncClient, auth_headers: dict, setup_export: dict):
    cid, yid = setup_export["client_id"], setup_export["fy_id"]
    await _create_and_generate(client, auth_headers, setup_export, numero="1")
    await _create_and_generate(client, auth_headers, setup_export, numero="2")

    resp = await client.get(
        f"/api/v1/clients/{cid}/fiscal-years/{yid}/fatture-pa-export", headers=auth_headers
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 2


async def test_zero_rate_line_gets_natura(client: AsyncClient, auth_headers: dict, setup_export: dict):
    cid, yid = setup_export["client_id"], setup_export["fy_id"]
    payload = _create_payload()
    payload["righe"] = [
        {
            "descrizione": "Prestazione esente",
            "quantita": "1",
            "prezzo_unitario": "500.00",
            "aliquota_iva": 0,
        }
    ]
    create_resp = await client.post(
        f"/api/v1/clients/{cid}/fiscal-years/{yid}/fatture-pa-export",
        json=payload,
        headers=auth_headers,
    )
    export_id = create_resp.json()["id"]

    gen_resp = await client.post(
        f"/api/v1/clients/{cid}/fiscal-years/{yid}/fatture-pa-export/{export_id}/generate-xml",
        headers=auth_headers,
    )
    assert gen_resp.status_code == 200, gen_resp.text

    dl_resp = await client.get(
        f"/api/v1/clients/{cid}/fiscal-years/{yid}/fatture-pa-export/{export_id}/download",
        headers=auth_headers,
    )
    root = ET.fromstring(dl_resp.content)
    natura = root.find(".//Natura")
    assert natura is not None
    assert natura.text == "N2.2"
