"""
FatturaPA Service — Import e parsing fatture elettroniche SDI (formato XML).

Supporta sia il namespace standard FatturaPA:
  {http://ivaservizi.agenziaentrate.gov.it/docs/xsd/fatture/v1.2}
che XML senza namespace.
"""
import uuid
import xml.etree.ElementTree as ET
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.tax import FatturaPAImport
from app.models.journal import JournalEntry, JournalLine, SequenceCounter
from app.schemas.tax import FatturaPAImportIn

STUDIO_UUID = uuid.UUID(settings.STUDIO_ID)

# Namespace FatturaPA standard
_NS_STD = "http://ivaservizi.agenziaentrate.gov.it/docs/xsd/fatture/v1.2"

TWO_PLACES = Decimal("0.01")


def _find_text(root: ET.Element, path: str, ns: Optional[str]) -> Optional[str]:
    """
    Cerca un elemento nel tree XML, provando prima con namespace poi senza.
    Restituisce il testo dell'elemento o None.
    """
    if ns:
        # Prova con namespace
        ns_path = "/".join(f"{{{ns}}}{part}" for part in path.split("/"))
        el = root.find(ns_path)
        if el is not None and el.text:
            return el.text.strip()

    # Prova senza namespace
    el = root.find(path)
    if el is not None and el.text:
        return el.text.strip()

    return None


def _find_all(root: ET.Element, path: str, ns: Optional[str]) -> List[ET.Element]:
    """Cerca tutti gli elementi con o senza namespace."""
    if ns:
        ns_path = "/".join(f"{{{ns}}}{part}" for part in path.split("/"))
        els = root.findall(ns_path)
        if els:
            return els

    return root.findall(path)


def _detect_namespace(root: ET.Element) -> Optional[str]:
    """Rileva il namespace dell'elemento root."""
    tag = root.tag
    if tag.startswith("{"):
        ns = tag[1:tag.index("}")]
        return ns
    return None


def parse_fattura_pa(xml_content: str) -> dict:
    """
    Parsa un FatturaPA XML (formato SDI italiano).

    Estrae:
    - cedente_prestatore: denominazione o nome+cognome del mittente
    - numero_fattura
    - data_fattura
    - imponibile_totale: somma di tutti i DatiRiepilogo/ImponibileImporto
    - iva_totale: somma di tutti i DatiRiepilogo/Imposta
    - totale_documento: ImportoTotaleDocumento

    Gestisce sia il namespace FatturaPA standard che XML senza namespace.
    """
    root = ET.fromstring(xml_content)
    ns = _detect_namespace(root)

    # Denominazione cedente
    denominazione = _find_text(
        root,
        "FatturaElettronicaHeader/CedentePrestatore/DatiAnagrafici/Anagrafica/Denominazione",
        ns,
    )
    if not denominazione:
        nome = _find_text(
            root,
            "FatturaElettronicaHeader/CedentePrestatore/DatiAnagrafici/Anagrafica/Nome",
            ns,
        )
        cognome = _find_text(
            root,
            "FatturaElettronicaHeader/CedentePrestatore/DatiAnagrafici/Anagrafica/Cognome",
            ns,
        )
        if nome or cognome:
            denominazione = f"{nome or ''} {cognome or ''}".strip()

    # Dati generali documento
    numero_fattura = _find_text(
        root,
        "FatturaElettronicaBody/DatiGenerali/DatiGeneraliDocumento/Numero",
        ns,
    )
    data_fattura = _find_text(
        root,
        "FatturaElettronicaBody/DatiGenerali/DatiGeneraliDocumento/Data",
        ns,
    )
    totale_doc_str = _find_text(
        root,
        "FatturaElettronicaBody/DatiGenerali/DatiGeneraliDocumento/ImportoTotaleDocumento",
        ns,
    )

    # DatiRiepilogo (possono essere multipli)
    imponibile_totale = Decimal("0")
    iva_totale = Decimal("0")

    # Cerca tutti i DatiRiepilogo
    riepilogos = _find_all(root, "FatturaElettronicaBody/DatiBeniServizi/DatiRiepilogo", ns)
    for riep in riepilogos:
        imponibile_el = riep.find(f"{{{ns}}}ImponibileImporto" if ns else "ImponibileImporto")
        imposta_el = riep.find(f"{{{ns}}}Imposta" if ns else "Imposta")
        if imponibile_el is not None and imponibile_el.text:
            imponibile_totale += Decimal(imponibile_el.text.strip())
        if imposta_el is not None and imposta_el.text:
            iva_totale += Decimal(imposta_el.text.strip())

    totale_documento = Decimal(totale_doc_str) if totale_doc_str else None

    return {
        "cedente_prestatore": denominazione,
        "numero_fattura": numero_fattura,
        "data_fattura": data_fattura,
        "imponibile_totale": str(imponibile_totale.quantize(TWO_PLACES)),
        "iva_totale": str(iva_totale.quantize(TWO_PLACES)),
        "totale_documento": str(totale_documento.quantize(TWO_PLACES)) if totale_documento is not None else None,
    }


async def import_fattura(
    db: AsyncSession,
    client_entity_id: uuid.UUID,
    fiscal_year_id: uuid.UUID,
    filename: str,
    xml_content: str,
    created_by: Optional[uuid.UUID] = None,
) -> FatturaPAImport:
    """
    1. Parsa il XML FatturaPA.
    2. Crea FatturaPAImport con stato='importata' e parsed_data.
    3. Se il parsing fallisce → stato='errore', errore_msg=str(exception).
    4. NON crea automaticamente JournalEntry.
    """
    parsed_data = None
    stato = "importata"
    errore_msg = None

    try:
        parsed_data = parse_fattura_pa(xml_content)
    except Exception as exc:
        stato = "errore"
        errore_msg = str(exc)[:500]

    imp = FatturaPAImport(
        id=uuid.uuid4(),
        studio_id=STUDIO_UUID,
        client_entity_id=client_entity_id,
        fiscal_year_id=fiscal_year_id,
        filename=filename,
        xml_content=xml_content,
        parsed_data=parsed_data,
        stato=stato,
        errore_msg=errore_msg,
    )
    db.add(imp)
    await db.flush()
    await db.refresh(imp)
    return imp


async def elaborate_fattura(
    db: AsyncSession,
    imp: FatturaPAImport,
    account_id_fornitore: uuid.UUID,
    account_id_iva: uuid.UUID,
    account_id_debito: uuid.UUID,
    created_by: Optional[uuid.UUID] = None,
) -> tuple:
    """
    Crea una JournalEntry bozza da una FatturaPAImport.
    Imposta imp.stato='elaborata' e imp.journal_entry_id.

    Returns: (FatturaPAImport, JournalEntry)
    """
    if imp.stato != "importata":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"La fattura non è in stato 'importata' (stato: {imp.stato})",
        )

    if imp.parsed_data is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La fattura non ha dati parsati — verificare che sia stata importata correttamente",
        )

    parsed = imp.parsed_data
    imponibile = Decimal(str(parsed.get("imponibile_totale", "0")))
    iva = Decimal(str(parsed.get("iva_totale", "0")))
    totale = imponibile + iva

    numero_str = parsed.get("numero_fattura") or "?"
    descrizione = f"Fattura {imp.filename} - {parsed.get('cedente_prestatore', '')} n.{numero_str}"[:500]

    # Usa il sequence counter per il numero registrazione
    from app.services.journal_service import next_sequence
    numero = await next_sequence(db, STUDIO_UUID, imp.client_entity_id, imp.fiscal_year_id)

    data_reg = date.today()
    if parsed.get("data_fattura"):
        try:
            from datetime import datetime
            data_reg = datetime.strptime(parsed["data_fattura"], "%Y-%m-%d").date()
        except (ValueError, TypeError):
            pass

    entry = JournalEntry(
        id=uuid.uuid4(),
        studio_id=STUDIO_UUID,
        client_entity_id=imp.client_entity_id,
        fiscal_year_id=imp.fiscal_year_id,
        numero_registrazione=numero,
        data_registrazione=data_reg,
        descrizione=descrizione,
        causale="FA",
        stato="draft",
        created_by=created_by,
    )
    db.add(entry)
    await db.flush()

    # Riga costo fornitore (dare)
    if imponibile > Decimal("0"):
        db.add(JournalLine(
            id=uuid.uuid4(),
            studio_id=STUDIO_UUID,
            journal_entry_id=entry.id,
            account_id=account_id_fornitore,
            dare=imponibile,
            avere=Decimal("0"),
            descrizione="Costo fornitore",
        ))

    # Riga IVA a credito (dare)
    if iva > Decimal("0"):
        db.add(JournalLine(
            id=uuid.uuid4(),
            studio_id=STUDIO_UUID,
            journal_entry_id=entry.id,
            account_id=account_id_iva,
            dare=iva,
            avere=Decimal("0"),
            descrizione="IVA acquisti",
        ))

    # Riga debito fornitore (avere)
    if totale > Decimal("0"):
        db.add(JournalLine(
            id=uuid.uuid4(),
            studio_id=STUDIO_UUID,
            journal_entry_id=entry.id,
            account_id=account_id_debito,
            dare=Decimal("0"),
            avere=totale,
            descrizione="Debito fornitore",
        ))

    await db.flush()

    # Aggiorna import
    imp.stato = "elaborata"
    imp.journal_entry_id = entry.id
    await db.flush()
    await db.refresh(imp)
    await db.refresh(entry)

    return imp, entry


async def list_imports(
    db: AsyncSession,
    client_entity_id: uuid.UUID,
    fiscal_year_id: uuid.UUID,
    stato: Optional[str] = None,
) -> List[FatturaPAImport]:
    """Lista import per cliente/esercizio."""
    query = select(FatturaPAImport).where(
        FatturaPAImport.studio_id == STUDIO_UUID,
        FatturaPAImport.client_entity_id == client_entity_id,
        FatturaPAImport.fiscal_year_id == fiscal_year_id,
    )
    if stato is not None:
        query = query.where(FatturaPAImport.stato == stato)
    query = query.order_by(FatturaPAImport.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_import(
    db: AsyncSession,
    client_entity_id: uuid.UUID,
    fiscal_year_id: uuid.UUID,
    import_id: uuid.UUID,
) -> Optional[FatturaPAImport]:
    result = await db.execute(
        select(FatturaPAImport).where(
            FatturaPAImport.id == import_id,
            FatturaPAImport.studio_id == STUDIO_UUID,
            FatturaPAImport.client_entity_id == client_entity_id,
            FatturaPAImport.fiscal_year_id == fiscal_year_id,
        )
    )
    return result.scalar_one_or_none()
