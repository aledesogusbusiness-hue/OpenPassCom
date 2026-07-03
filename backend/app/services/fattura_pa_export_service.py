"""
FatturaPA Export Service — Emissione fatture elettroniche verso SDI (Phase 9).

Infrastruttura lato nostro: genera XML FatturaPA v1.2 (formato FPR12) valido
nella struttura, pronto per essere trasmesso a SDI tramite un canale esterno
(intermediario accreditato, PEC, o un futuro connettore diretto). L'invio
vero e proprio e la ricezione dell'esito NON sono automatizzati qui — vanno
registrati manualmente con mark_inviata()/mark_esito(), stesso punto di
innesto che userebbe un connettore reale in futuro.

REGOLA: usa sempre `from sqlalchemy import Uuid` per i modelli (già rispettata
         in models/tax.py). Qui solo servizio, nessun modello.
"""
import uuid
import xml.etree.ElementTree as ET
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import func as sqlfunc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.parties import ClientEntity
from app.models.tax import FatturaPAExport, FatturaPAExportLine
from app.schemas.tax import FatturaPAExportCreate

STUDIO_UUID = uuid.UUID(settings.STUDIO_ID)

_NS = "http://ivaservizi.agenziaentrate.gov.it/docs/xsd/fatture/v1.2"
_TWO_PLACES = Decimal("0.01")

_REGIME_FISCALE_MAP = {
    "ordinario": "RF01",
    "semplificato": "RF01",
    "forfettario": "RF19",
}


def _q(value: Decimal) -> str:
    return str(value.quantize(_TWO_PLACES, rounding=ROUND_HALF_UP))


async def create_export(
    db: AsyncSession,
    client_id: uuid.UUID,
    fiscal_year_id: uuid.UUID,
    data: FatturaPAExportCreate,
    created_by: uuid.UUID,
) -> FatturaPAExport:
    export = FatturaPAExport(
        id=uuid.uuid4(),
        studio_id=STUDIO_UUID,
        client_entity_id=client_id,
        fiscal_year_id=fiscal_year_id,
        journal_entry_id=data.journal_entry_id,
        tipo_documento=data.tipo_documento,
        numero_fattura=data.numero_fattura,
        data_fattura=data.data_fattura,
        cedente_indirizzo=data.cedente_indirizzo,
        cedente_cap=data.cedente_cap,
        cedente_comune=data.cedente_comune,
        cedente_provincia=data.cedente_provincia.upper(),
        destinatario_denominazione=data.destinatario_denominazione,
        destinatario_partita_iva=data.destinatario_partita_iva,
        destinatario_codice_fiscale=data.destinatario_codice_fiscale,
        destinatario_indirizzo=data.destinatario_indirizzo,
        destinatario_cap=data.destinatario_cap,
        destinatario_comune=data.destinatario_comune,
        destinatario_provincia=data.destinatario_provincia.upper(),
        destinatario_codice_sdi=data.destinatario_codice_sdi or "0000000",
        destinatario_pec=data.destinatario_pec,
        stato="bozza",
        created_by=created_by,
    )
    db.add(export)
    await db.flush()

    for i, riga in enumerate(data.righe, start=1):
        db.add(FatturaPAExportLine(
            id=uuid.uuid4(),
            studio_id=STUDIO_UUID,
            fattura_pa_export_id=export.id,
            numero_linea=i,
            descrizione=riga.descrizione,
            quantita=riga.quantita,
            unita_misura=riga.unita_misura,
            prezzo_unitario=riga.prezzo_unitario,
            aliquota_iva=Decimal(riga.aliquota_iva),
        ))

    await db.flush()
    await db.refresh(export)
    return export


async def get_lines(db: AsyncSession, export_id: uuid.UUID) -> List[FatturaPAExportLine]:
    result = await db.execute(
        select(FatturaPAExportLine)
        .where(FatturaPAExportLine.fattura_pa_export_id == export_id)
        .order_by(FatturaPAExportLine.numero_linea)
    )
    return list(result.scalars().all())


async def _next_progressivo_invio(db: AsyncSession) -> str:
    result = await db.execute(
        select(sqlfunc.count(FatturaPAExport.id)).where(
            FatturaPAExport.studio_id == STUDIO_UUID,
            FatturaPAExport.progressivo_invio.isnot(None),
        )
    )
    count = result.scalar_one()
    return f"{count + 1:05d}"


def _sub(parent: ET.Element, tag: str, text: Optional[str] = None) -> ET.Element:
    el = ET.SubElement(parent, tag)
    if text is not None:
        el.text = text
    return el


def build_fattura_xml(
    client: ClientEntity,
    export: FatturaPAExport,
    lines: List[FatturaPAExportLine],
    progressivo_invio: str,
) -> str:
    """Costruisce l'XML FatturaPA v1.2 (formato FPR12) per una fattura emessa."""
    ET.register_namespace("p", _NS)
    root = ET.Element(f"{{{_NS}}}FatturaElettronica", {"versione": "FPR12"})

    # ── Header ──────────────────────────────────────────────────────────────
    header = _sub(root, "FatturaElettronicaHeader")

    dati_trasm = _sub(header, "DatiTrasmissione")
    id_trasm = _sub(dati_trasm, "IdTrasmittente")
    _sub(id_trasm, "IdPaese", "IT")
    _sub(id_trasm, "IdCodice", client.partita_iva or client.codice_fiscale or "")
    _sub(dati_trasm, "ProgressivoInvio", progressivo_invio)
    _sub(dati_trasm, "FormatoTrasmissione", "FPR12")
    _sub(dati_trasm, "CodiceDestinatario", export.destinatario_codice_sdi)
    if export.destinatario_pec:
        _sub(dati_trasm, "PECDestinatario", export.destinatario_pec)

    cedente = _sub(header, "CedentePrestatore")
    cedente_anag = _sub(cedente, "DatiAnagrafici")
    if client.partita_iva:
        id_fiscale = _sub(cedente_anag, "IdFiscaleIVA")
        _sub(id_fiscale, "IdPaese", "IT")
        _sub(id_fiscale, "IdCodice", client.partita_iva)
    if client.codice_fiscale:
        _sub(cedente_anag, "CodiceFiscale", client.codice_fiscale)
    anagrafica = _sub(cedente_anag, "Anagrafica")
    _sub(anagrafica, "Denominazione", client.ragione_sociale)
    _sub(cedente_anag, "RegimeFiscale", _REGIME_FISCALE_MAP.get(client.fiscal_regime, "RF01"))
    sede_cedente = _sub(cedente, "Sede")
    _sub(sede_cedente, "Indirizzo", export.cedente_indirizzo)
    _sub(sede_cedente, "CAP", export.cedente_cap)
    _sub(sede_cedente, "Comune", export.cedente_comune)
    _sub(sede_cedente, "Provincia", export.cedente_provincia)
    _sub(sede_cedente, "Nazione", "IT")

    cessionario = _sub(header, "CessionarioCommittente")
    cess_anag = _sub(cessionario, "DatiAnagrafici")
    if export.destinatario_partita_iva:
        id_fiscale_c = _sub(cess_anag, "IdFiscaleIVA")
        _sub(id_fiscale_c, "IdPaese", "IT")
        _sub(id_fiscale_c, "IdCodice", export.destinatario_partita_iva)
    if export.destinatario_codice_fiscale:
        _sub(cess_anag, "CodiceFiscale", export.destinatario_codice_fiscale)
    anagrafica_c = _sub(cess_anag, "Anagrafica")
    _sub(anagrafica_c, "Denominazione", export.destinatario_denominazione)
    sede_c = _sub(cessionario, "Sede")
    _sub(sede_c, "Indirizzo", export.destinatario_indirizzo)
    _sub(sede_c, "CAP", export.destinatario_cap)
    _sub(sede_c, "Comune", export.destinatario_comune)
    _sub(sede_c, "Provincia", export.destinatario_provincia)
    _sub(sede_c, "Nazione", "IT")

    # ── Body ────────────────────────────────────────────────────────────────
    body = _sub(root, "FatturaElettronicaBody")

    dati_generali = _sub(body, "DatiGenerali")
    dgd = _sub(dati_generali, "DatiGeneraliDocumento")
    _sub(dgd, "TipoDocumento", export.tipo_documento)
    _sub(dgd, "Divisa", "EUR")
    _sub(dgd, "Data", export.data_fattura.isoformat())
    _sub(dgd, "Numero", export.numero_fattura)

    riepilogo_per_aliquota: dict[Decimal, dict[str, Decimal]] = {}
    totale_documento = Decimal("0")

    dati_beni = _sub(body, "DatiBeniServizi")
    for line in lines:
        prezzo_totale = (line.quantita * line.prezzo_unitario).quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)
        dettaglio = _sub(dati_beni, "DettaglioLinee")
        _sub(dettaglio, "NumeroLinea", str(line.numero_linea))
        _sub(dettaglio, "Descrizione", line.descrizione)
        _sub(dettaglio, "Quantita", _q(line.quantita))
        if line.unita_misura:
            _sub(dettaglio, "UnitaMisura", line.unita_misura)
        _sub(dettaglio, "PrezzoUnitario", _q(line.prezzo_unitario))
        _sub(dettaglio, "PrezzoTotale", _q(prezzo_totale))
        _sub(dettaglio, "AliquotaIVA", _q(line.aliquota_iva))

        agg = riepilogo_per_aliquota.setdefault(
            line.aliquota_iva, {"imponibile": Decimal("0"), "imposta": Decimal("0")}
        )
        agg["imponibile"] += prezzo_totale
        imposta_riga = (prezzo_totale * line.aliquota_iva / Decimal("100")).quantize(
            _TWO_PLACES, rounding=ROUND_HALF_UP
        )
        agg["imposta"] += imposta_riga
        totale_documento += prezzo_totale + imposta_riga

    _sub(dgd, "ImportoTotaleDocumento", _q(totale_documento))

    for aliquota, tot in riepilogo_per_aliquota.items():
        riepilogo = _sub(dati_beni, "DatiRiepilogo")
        _sub(riepilogo, "AliquotaIVA", _q(aliquota))
        if aliquota == Decimal("0"):
            _sub(riepilogo, "Natura", "N2.2")  # non soggetta — placeholder, da verificare caso per caso
        _sub(riepilogo, "ImponibileImporto", _q(tot["imponibile"]))
        _sub(riepilogo, "Imposta", _q(tot["imposta"]))
        _sub(riepilogo, "EsigibilitaIVA", "I")

    xml_bytes = ET.tostring(root, encoding="UTF-8", xml_declaration=True)
    return xml_bytes.decode("utf-8")


async def generate_xml(db: AsyncSession, client: ClientEntity, export: FatturaPAExport) -> FatturaPAExport:
    if export.stato not in ("bozza", "errore"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Impossibile rigenerare l'XML da stato '{export.stato}'",
        )

    lines = await get_lines(db, export.id)
    if not lines:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La fattura non ha righe di dettaglio",
        )

    progressivo = await _next_progressivo_invio(db)

    try:
        xml_content = build_fattura_xml(client, export, lines, progressivo)
    except Exception as exc:
        export.stato = "errore"
        export.errore_msg = str(exc)[:500]
        await db.flush()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Errore nella generazione dell'XML: {exc}",
        )

    export.xml_content = xml_content
    export.progressivo_invio = progressivo
    export.stato = "generata"
    export.errore_msg = None
    await db.flush()
    await db.refresh(export)
    return export


async def mark_inviata(
    db: AsyncSession, export: FatturaPAExport, identificativo_sdi: Optional[str]
) -> FatturaPAExport:
    if export.stato != "generata":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Solo le fatture in stato 'generata' possono essere marcate come inviate (stato attuale: {export.stato})",
        )
    export.stato = "inviata"
    export.data_invio = datetime.now(timezone.utc)
    if identificativo_sdi:
        export.identificativo_sdi = identificativo_sdi
    await db.flush()
    await db.refresh(export)
    return export


async def mark_esito(
    db: AsyncSession, export: FatturaPAExport, esito: str, messaggio: Optional[str]
) -> FatturaPAExport:
    if export.stato != "inviata":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Solo le fatture in stato 'inviata' possono ricevere un esito (stato attuale: {export.stato})",
        )
    export.stato = esito
    export.data_esito = datetime.now(timezone.utc)
    export.esito_messaggio = messaggio
    await db.flush()
    await db.refresh(export)
    return export


async def list_exports(
    db: AsyncSession,
    client_id: uuid.UUID,
    fiscal_year_id: uuid.UUID,
    stato: Optional[str] = None,
) -> List[FatturaPAExport]:
    query = select(FatturaPAExport).where(
        FatturaPAExport.studio_id == STUDIO_UUID,
        FatturaPAExport.client_entity_id == client_id,
        FatturaPAExport.fiscal_year_id == fiscal_year_id,
    )
    if stato is not None:
        query = query.where(FatturaPAExport.stato == stato)
    query = query.order_by(FatturaPAExport.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_export(
    db: AsyncSession,
    client_id: uuid.UUID,
    fiscal_year_id: uuid.UUID,
    export_id: uuid.UUID,
) -> Optional[FatturaPAExport]:
    result = await db.execute(
        select(FatturaPAExport).where(
            FatturaPAExport.id == export_id,
            FatturaPAExport.studio_id == STUDIO_UUID,
            FatturaPAExport.client_entity_id == client_id,
            FatturaPAExport.fiscal_year_id == fiscal_year_id,
        )
    )
    return result.scalar_one_or_none()
