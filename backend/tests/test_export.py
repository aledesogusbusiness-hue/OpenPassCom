"""
Test Phase 7 — Export PDF/Excel bilancio e libro giornale.
"""
import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.accounting import AccountPlan, Account

pytestmark = pytest.mark.asyncio

STUDIO_ID = uuid.UUID(settings.STUDIO_ID)

AT_SP_A = uuid.UUID("10000000-0000-0000-0000-000000000001")
AT_SP_P = uuid.UUID("10000000-0000-0000-0000-000000000002")
AT_CE_C = uuid.UUID("10000000-0000-0000-0000-000000000003")
AT_CE_R = uuid.UUID("10000000-0000-0000-0000-000000000004")


@pytest_asyncio.fixture()
async def setup_export(client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
    resp = await client.post(
        "/api/v1/clients",
        json={
            "ragione_sociale": "Test Export S.r.l.",
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

    plan_id = uuid.uuid4()
    db_session.add(AccountPlan(
        id=plan_id, studio_id=STUDIO_ID, client_entity_id=client_id,
        nome="Piano Export Test", is_default=True,
    ))

    cassa_id = uuid.uuid4()
    ricavi_id = uuid.uuid4()

    db_session.add(Account(
        id=cassa_id, studio_id=STUDIO_ID, account_plan_id=plan_id,
        account_type_id=AT_SP_A, codice="1001", nome="Cassa", livello=1,
    ))
    db_session.add(Account(
        id=ricavi_id, studio_id=STUDIO_ID, account_plan_id=plan_id,
        account_type_id=AT_CE_R, codice="4001", nome="Ricavi Vendite", livello=1,
    ))
    await db_session.flush()

    entry_resp = await client.post(
        f"/api/v1/clients/{client_id}/fiscal-years/{fy_id}/journal-entries",
        json={
            "data_registrazione": "2024-06-30",
            "descrizione": "Vendita test",
            "causale": "FV",
            "lines": [
                {"account_id": str(cassa_id), "dare": "1000.00", "avere": "0"},
                {"account_id": str(ricavi_id), "dare": "0", "avere": "1000.00"},
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

    return {"client_id": str(client_id), "fy_id": str(fy_id)}


async def test_export_bilancio_pdf(client: AsyncClient, auth_headers: dict, setup_export: dict):
    cid, yid = setup_export["client_id"], setup_export["fy_id"]

    resp = await client.get(
        f"/api/v1/clients/{cid}/fiscal-years/{yid}/export/bilancio?format=pdf",
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content.startswith(b"%PDF")
    assert len(resp.content) > 500


async def test_export_bilancio_xlsx(client: AsyncClient, auth_headers: dict, setup_export: dict):
    cid, yid = setup_export["client_id"], setup_export["fy_id"]

    resp = await client.get(
        f"/api/v1/clients/{cid}/fiscal-years/{yid}/export/bilancio?format=xlsx",
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    assert "spreadsheetml" in resp.headers["content-type"]
    # Il formato xlsx è uno zip: firma PK
    assert resp.content.startswith(b"PK")


async def test_export_bilancio_default_format_is_pdf(
    client: AsyncClient, auth_headers: dict, setup_export: dict
):
    cid, yid = setup_export["client_id"], setup_export["fy_id"]

    resp = await client.get(
        f"/api/v1/clients/{cid}/fiscal-years/{yid}/export/bilancio",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"


async def test_export_libro_giornale_pdf(client: AsyncClient, auth_headers: dict, setup_export: dict):
    cid, yid = setup_export["client_id"], setup_export["fy_id"]

    resp = await client.get(
        f"/api/v1/clients/{cid}/fiscal-years/{yid}/export/libro-giornale?format=pdf",
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content.startswith(b"%PDF")


async def test_export_libro_giornale_xlsx(client: AsyncClient, auth_headers: dict, setup_export: dict):
    cid, yid = setup_export["client_id"], setup_export["fy_id"]

    resp = await client.get(
        f"/api/v1/clients/{cid}/fiscal-years/{yid}/export/libro-giornale?format=xlsx",
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    assert "spreadsheetml" in resp.headers["content-type"]
    assert resp.content.startswith(b"PK")


async def test_export_bilancio_client_not_found(client: AsyncClient, auth_headers: dict):
    fake_id = uuid.uuid4()
    resp = await client.get(
        f"/api/v1/clients/{fake_id}/fiscal-years/{fake_id}/export/bilancio",
        headers=auth_headers,
    )
    assert resp.status_code == 404


async def test_export_requires_auth(client: AsyncClient, setup_export: dict):
    """Senza token restituisce 403 (HTTPBearer rifiuta)."""
    cid, yid = setup_export["client_id"], setup_export["fy_id"]
    resp = await client.get(
        f"/api/v1/clients/{cid}/fiscal-years/{yid}/export/bilancio",
    )
    assert resp.status_code == 403
