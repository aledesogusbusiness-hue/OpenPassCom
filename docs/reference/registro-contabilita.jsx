import { useState, useEffect, useMemo, useRef } from "react";

/* ================================================================
   REGISTRO CONTABILITÀ — Piattaforma operativa per lo studio
   Partita doppia · Prima nota con causali guidate · Libro giornale
   Mastrini · Bilancio di verifica · Registri e liquidazione IVA
   Scadenzario con incassi/pagamenti · Multi-azienda · Audit trail
   Regole: quadratura obbligatoria D/A · nessuna cancellazione di
   movimenti registrati (solo storno tracciato) · numerazioni coerenti
   ================================================================ */

const C = {
  carta: "#F2F1EB", cartaScura: "#E9E8DF", inchiostro: "#1C241F",
  tenue: "#5A6159", verde: "#1E5C46", verdeCh: "#E1EAE3",
  ambra: "#B0761C", ambraCh: "#F3E8D2", rosso: "#A32C22",
  rossoCh: "#F0DEDA", linea: "#D6D4C8", bianco: "#FBFAF6", blu: "#2C4A6E",
};

const r2 = (v) => Math.round((v + Number.EPSILON) * 100) / 100;
const fmtE = (v) => new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR" }).format(v || 0);
const fmtD = (iso) => (iso ? iso.split("-").reverse().join("/") : "—");
const oggi = () => new Date().toISOString().slice(0, 10);
const uid = () => Math.random().toString(36).slice(2, 10);

const ALIQUOTE = [22, 10, 5, 4, 0];
const MESI_N = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"];

/* ---------------- Piano dei conti (schema CEE compatto) ---------------- */
const PIANO_CONTI_BASE = [
  ["01.01", "Cassa contanti", "SP-A"],
  ["01.02", "Banca c/c", "SP-A"],
  ["02.01", "Crediti v/clienti", "SP-A"],
  ["02.05", "Crediti v/erario", "SP-A"],
  ["03.01", "IVA a credito (ns/credito)", "SP-A"],
  ["04.01", "Impianti e macchinari", "SP-A"],
  ["04.02", "Attrezzature", "SP-A"],
  ["04.05", "F.do ammortamento", "SP-P"],
  ["10.01", "Debiti v/fornitori", "SP-P"],
  ["10.02", "IVA a debito (ns/debito)", "SP-P"],
  ["10.03", "Erario c/IVA (liquidazione)", "SP-P"],
  ["10.04", "Debiti tributari", "SP-P"],
  ["10.05", "Debiti v/istituti previdenziali", "SP-P"],
  ["11.01", "Capitale sociale", "SP-P"],
  ["11.02", "Utili (perdite) a nuovo", "SP-P"],
  ["12.01", "Mutui passivi", "SP-P"],
  ["20.01", "Acquisti merci e materie", "CE-C"],
  ["20.02", "Costi per servizi", "CE-C"],
  ["20.03", "Godimento beni di terzi", "CE-C"],
  ["20.04", "Salari e stipendi", "CE-C"],
  ["20.05", "Oneri sociali", "CE-C"],
  ["20.06", "Ammortamenti", "CE-C"],
  ["20.07", "Oneri finanziari", "CE-C"],
  ["20.08", "Oneri diversi di gestione", "CE-C"],
  ["30.01", "Ricavi vendite merci", "CE-R"],
  ["30.02", "Ricavi prestazioni di servizi", "CE-R"],
  ["30.03", "Altri ricavi e proventi", "CE-R"],
].map(([codice, nome, tipo]) => ({ codice, nome, tipo }));

const TIPO_NOME = { "SP-A": "Attivo", "SP-P": "Passivo", "CE-C": "Costi", "CE-R": "Ricavi" };

/* ---------------- Causali ---------------- */
const CAUSALI = [
  { id: "FV", nome: "Fattura di vendita", registroIva: "vendite", scadenza: "incasso" },
  { id: "FA", nome: "Fattura di acquisto", registroIva: "acquisti", scadenza: "pagamento" },
  { id: "IN", nome: "Incasso da cliente", registroIva: null, scadenza: null },
  { id: "PG", nome: "Pagamento a fornitore", registroIva: null, scadenza: null },
  { id: "PN", nome: "Prima nota libera (manuale)", registroIva: null, scadenza: null },
];

/* ---------------- Dati dimostrativi ---------------- */
function datiDemo() {
  const az1 = { id: "az1", nome: "Impianti Meloni S.r.l.", piva: "02345670926", regime: "Ordinario", periodicitaIva: "mensile", esercizio: "2026" };
  const az2 = { id: "az2", nome: "Studio Grafico Pilia", piva: "03456780927", regime: "Semplificato", periodicitaIva: "trimestrale", esercizio: "2026" };
  const controparti = [
    { id: "c1", nome: "Edilizia Sarda S.p.A.", piva: "01234560928", tipo: "cliente", aziendaId: "az1" },
    { id: "c2", nome: "Hotel Miramare S.r.l.", piva: "01987650929", tipo: "cliente", aziendaId: "az1" },
    { id: "f1", nome: "Ferramenta Corso S.n.c.", piva: "02876540921", tipo: "fornitore", aziendaId: "az1" },
    { id: "f2", nome: "Enel Energia S.p.A.", piva: "06655971007", tipo: "fornitore", aziendaId: "az1" },
    { id: "f3", nome: "TIM Business", piva: "00488410010", tipo: "fornitore", aziendaId: "az1" },
    { id: "c3", nome: "Cantina Argiolas", piva: "01115640925", tipo: "cliente", aziendaId: "az2" },
  ];
  const M = (n, data, causaleId, descrizione, righe, extra = {}) => ({
    id: uid(), aziendaId: "az1", numero: n, data, causaleId, descrizione,
    stato: "registrata", righe, creatoIl: data + "T09:00", operatore: "demo", ...extra,
  });
  const movimenti = [
    M(1, "2026-01-01", "PN", "Apertura conti esercizio 2026", [
      { conto: "01.02", dare: 24000, avere: 0 }, { conto: "01.01", dare: 800, avere: 0 },
      { conto: "04.01", dare: 15000, avere: 0 },
      { conto: "11.01", dare: 0, avere: 20000 }, { conto: "11.02", dare: 0, avere: 7300 },
      { conto: "12.01", dare: 0, avere: 12500 },
    ]),
    M(2, "2026-04-20", "FV", "Fatt. 11/2026 — Edilizia Sarda S.p.A.", [
      { conto: "02.01", dare: 6100, avere: 0 }, { conto: "30.02", dare: 0, avere: 5000 },
      { conto: "10.02", dare: 0, avere: 1100 },
    ], { iva: { registro: "vendite", protocollo: 11, numDoc: "11/2026", dataDoc: "2026-04-20", controparteId: "c1", imponibile: 5000, aliquota: 22, imposta: 1100 },
        scadenza: { data: "2026-05-20", importo: 6100, tipo: "incasso", saldata: true } }),
    M(3, "2026-05-10", "FA", "Fatt. 887 — Ferramenta Corso S.n.c.", [
      { conto: "20.01", dare: 1500, avere: 0 }, { conto: "03.01", dare: 330, avere: 0 },
      { conto: "10.01", dare: 0, avere: 1830 },
    ], { iva: { registro: "acquisti", protocollo: 1, numDoc: "887", dataDoc: "2026-05-08", controparteId: "f1", imponibile: 1500, aliquota: 22, imposta: 330 },
        scadenza: { data: "2026-06-09", importo: 1830, tipo: "pagamento", saldata: true } }),
    M(4, "2026-05-15", "FV", "Fatt. 12/2026 — Edilizia Sarda S.p.A.", [
      { conto: "02.01", dare: 10248, avere: 0 }, { conto: "30.02", dare: 0, avere: 8400 },
      { conto: "10.02", dare: 0, avere: 1848 },
    ], { iva: { registro: "vendite", protocollo: 12, numDoc: "12/2026", dataDoc: "2026-05-15", controparteId: "c1", imponibile: 8400, aliquota: 22, imposta: 1848 },
        scadenza: { data: "2026-06-14", importo: 10248, tipo: "incasso", saldata: false } }),
    M(5, "2026-05-22", "IN", "Incasso fatt. 11/2026 — Edilizia Sarda", [
      { conto: "01.02", dare: 6100, avere: 0 }, { conto: "02.01", dare: 0, avere: 6100 },
    ]),
    M(6, "2026-06-03", "FA", "Fatt. 4456120 — Enel Energia", [
      { conto: "20.02", dare: 640, avere: 0 }, { conto: "03.01", dare: 140.8, avere: 0 },
      { conto: "10.01", dare: 0, avere: 780.8 },
    ], { iva: { registro: "acquisti", protocollo: 2, numDoc: "4456120", dataDoc: "2026-06-01", controparteId: "f2", imponibile: 640, aliquota: 22, imposta: 140.8 },
        scadenza: { data: "2026-07-03", importo: 780.8, tipo: "pagamento", saldata: false } }),
    M(7, "2026-06-05", "FV", "Fatt. 13/2026 — Hotel Miramare", [
      { conto: "02.01", dare: 3904, avere: 0 }, { conto: "30.02", dare: 0, avere: 3200 },
      { conto: "10.02", dare: 0, avere: 704 },
    ], { iva: { registro: "vendite", protocollo: 13, numDoc: "13/2026", dataDoc: "2026-06-05", controparteId: "c2", imponibile: 3200, aliquota: 22, imposta: 704 },
        scadenza: { data: "2026-07-05", importo: 3904, tipo: "incasso", saldata: false } }),
    M(8, "2026-06-09", "PG", "Pagamento fatt. 887 — Ferramenta Corso", [
      { conto: "10.01", dare: 1830, avere: 0 }, { conto: "01.02", dare: 0, avere: 1830 },
    ]),
    M(9, "2026-06-12", "FA", "Fatt. 99213 — TIM Business", [
      { conto: "20.02", dare: 240, avere: 0 }, { conto: "03.01", dare: 52.8, avere: 0 },
      { conto: "10.01", dare: 0, avere: 292.8 },
    ], { iva: { registro: "acquisti", protocollo: 3, numDoc: "99213", dataDoc: "2026-06-10", controparteId: "f3", imponibile: 240, aliquota: 22, imposta: 52.8 },
        scadenza: { data: "2026-07-12", importo: 292.8, tipo: "pagamento", saldata: false } }),
  ];
  return { aziende: [az1, az2], controparti, movimenti, contiExtra: [] };
}

/* ---------------- componenti UI ---------------- */
function Pill({ tono = "ok", children }) {
  const m = { ok: [C.verdeCh, C.verde], warn: [C.ambraCh, C.ambra], ko: [C.rossoCh, C.rosso], info: ["#E3E9F0", C.blu], neutro: [C.cartaScura, C.tenue] };
  const [bg, fg] = m[tono];
  return <span style={{ background: bg, color: fg, fontFamily: "'Spline Sans Mono',monospace", fontSize: 10.5, letterSpacing: ".07em", padding: "3px 9px", borderRadius: 3, textTransform: "uppercase", whiteSpace: "nowrap" }}>{children}</span>;
}
function Eyebrow({ children }) {
  return <div style={{ fontFamily: "'Spline Sans Mono',monospace", fontSize: 11, letterSpacing: ".22em", textTransform: "uppercase", color: C.tenue, marginBottom: 8 }}>{children}</div>;
}
function Titolo({ children }) {
  return <h2 style={{ fontFamily: "'Marcellus',serif", fontWeight: 400, fontSize: "clamp(24px,3.5vw,34px)", margin: "0 0 6px", lineHeight: 1.1 }}>{children}</h2>;
}
function Sotto({ children }) {
  return <p style={{ color: C.tenue, fontSize: 13.5, lineHeight: 1.6, margin: "0 0 22px", maxWidth: 740 }}>{children}</p>;
}

/* ================================================================ */
export default function RegistroContabilita() {
  const [db, setDb] = useState(null);          // {aziende, controparti, movimenti, contiExtra}
  const [azId, setAzId] = useState("az1");
  const [sez, setSez] = useState("dashboard");
  const [salvataggio, setSalvataggio] = useState("caricamento");
  const caricato = useRef(false);

  /* ---- persistenza ---- */
  useEffect(() => {
    (async () => {
      try {
        const r = await window.storage.get("registro-contabilita:v1");
        if (r && r.value) { setDb(JSON.parse(r.value)); setSalvataggio("salvato"); }
        else { setDb(datiDemo()); setSalvataggio("nuovo"); }
      } catch { setDb(datiDemo()); setSalvataggio("nuovo"); }
      caricato.current = true;
    })();
  }, []);
  useEffect(() => {
    if (!caricato.current || !db) return;
    setSalvataggio("in-corso");
    const t = setTimeout(async () => {
      try { await window.storage.set("registro-contabilita:v1", JSON.stringify(db)); setSalvataggio("salvato"); }
      catch { setSalvataggio("sessione"); }
    }, 600);
    return () => clearTimeout(t);
  }, [db]);

  /* ---- stato form prima nota ---- */
  const [causale, setCausale] = useState("FV");
  const [fDoc, setFDoc] = useState({ data: oggi(), numDoc: "", dataDoc: oggi(), controparteId: "", imponibile: "", aliquota: 22, contoEco: "", dataScadenza: "" });
  const [fMan, setFMan] = useState({ data: oggi(), descrizione: "", righe: [{ conto: "", dare: "", avere: "" }, { conto: "", dare: "", avere: "" }] });
  const [avviso, setAvviso] = useState(null);
  const [contoMastro, setContoMastro] = useState("01.02");
  const [regIvaVista, setRegIvaVista] = useState("vendite");
  const [periodoLiq, setPeriodoLiq] = useState(5); // indice mese 0-based (giugno=5) o trimestre
  const [creditoPrec, setCreditoPrec] = useState(0);
  const [nuovaCp, setNuovaCp] = useState({ nome: "", piva: "", tipo: "cliente" });
  const [nuovoConto, setNuovoConto] = useState({ codice: "", nome: "", tipo: "CE-C" });

  const az = db?.aziende.find((a) => a.id === azId);
  const conti = useMemo(() => db ? [...PIANO_CONTI_BASE, ...db.contiExtra.filter((c) => c.aziendaId === azId)] : PIANO_CONTI_BASE, [db, azId]);
  const contoNome = (cod) => { const c = conti.find((x) => x.codice === cod); return c ? c.nome : cod; };
  const cpDiAz = useMemo(() => db ? db.controparti.filter((c) => c.aziendaId === azId) : [], [db, azId]);
  const cpNome = (id) => db?.controparti.find((c) => c.id === id)?.nome || "—";

  const movs = useMemo(() => db ? db.movimenti.filter((m) => m.aziendaId === azId).sort((a, b) => a.data.localeCompare(b.data) || a.numero - b.numero) : [], [db, azId]);
  const postati = useMemo(() => movs.filter((m) => m.stato !== "bozza"), [movs]);

  /* ---- derivazioni contabili ---- */
  const saldi = useMemo(() => {
    const s = {};
    postati.forEach((m) => m.righe.forEach((r) => {
      if (!s[r.conto]) s[r.conto] = { dare: 0, avere: 0 };
      s[r.conto].dare = r2(s[r.conto].dare + (+r.dare || 0));
      s[r.conto].avere = r2(s[r.conto].avere + (+r.avere || 0));
    }));
    return s;
  }, [postati]);

  const scadenze = useMemo(() =>
    postati.filter((m) => m.scadenza).map((m) => ({ mov: m, ...m.scadenza }))
      .sort((a, b) => a.data.localeCompare(b.data)), [postati]);
  const scadAperte = scadenze.filter((s) => !s.saldata);

  const righeIva = (registro) => postati
    .filter((m) => m.iva && m.iva.registro === registro && m.stato !== "stornata")
    .sort((a, b) => a.iva.protocollo - b.iva.protocollo);

  const prossimoNumero = () => movs.reduce((mx, m) => Math.max(mx, m.numero), 0) + 1;
  const prossimoProt = (registro) => righeIva(registro).reduce((mx, m) => Math.max(mx, m.iva.protocollo), 0) + 1;

  /* ---- liquidazione IVA ---- */
  const liq = useMemo(() => {
    if (!az) return null;
    const mensile = az.periodicitaIva === "mensile";
    const mesi = mensile ? [periodoLiq] : [periodoLiq * 3, periodoLiq * 3 + 1, periodoLiq * 3 + 2];
    const inPeriodo = (m) => { const mm = +m.data.slice(5, 7) - 1; return m.data.slice(0, 4) === az.esercizio && mesi.includes(mm); };
    const vend = righeIva("vendite").filter(inPeriodo);
    const acq = righeIva("acquisti").filter(inPeriodo);
    const ivaDeb = r2(vend.reduce((s, m) => s + m.iva.imposta, 0));
    const ivaCred = r2(acq.reduce((s, m) => s + m.iva.imposta, 0));
    const saldo = r2(ivaDeb - ivaCred - (+creditoPrec || 0));
    return { mensile, mesi, vend, acq, ivaDeb, ivaCred, saldo };
  }, [az, postati, periodoLiq, creditoPrec]);

  /* ---- azioni ---- */
  const aggiungiMov = (mov) => setDb((p) => ({ ...p, movimenti: [...p.movimenti, mov] }));

  const registraDocumento = () => {
    const c = CAUSALI.find((x) => x.id === causale);
    const imp = r2(+fDoc.imponibile || 0);
    if (!imp || !fDoc.controparteId || !fDoc.contoEco) { setAvviso(["ko", "Compila controparte, conto economico e imponibile."]); return; }
    const iva = r2(imp * fDoc.aliquota / 100), tot = r2(imp + iva);
    const vendita = causale === "FV";
    const righe = vendita
      ? [{ conto: "02.01", dare: tot, avere: 0 }, { conto: fDoc.contoEco, dare: 0, avere: imp }, ...(iva ? [{ conto: "10.02", dare: 0, avere: iva }] : [])]
      : [{ conto: fDoc.contoEco, dare: imp, avere: 0 }, ...(iva ? [{ conto: "03.01", dare: iva, avere: 0 }] : []), { conto: "10.01", dare: 0, avere: tot }];
    const cp = cpNome(fDoc.controparteId);
    aggiungiMov({
      id: uid(), aziendaId: azId, numero: prossimoNumero(), data: fDoc.data, causaleId: causale,
      descrizione: `Fatt. ${fDoc.numDoc || "s.n."} — ${cp}`, stato: "registrata", righe,
      creatoIl: new Date().toISOString(), operatore: "studio",
      iva: { registro: c.registroIva, protocollo: prossimoProt(c.registroIva), numDoc: fDoc.numDoc, dataDoc: fDoc.dataDoc, controparteId: fDoc.controparteId, imponibile: imp, aliquota: fDoc.aliquota, imposta: iva },
      scadenza: { data: fDoc.dataScadenza || fDoc.data, importo: tot, tipo: c.scadenza, saldata: false },
    });
    setFDoc({ data: oggi(), numDoc: "", dataDoc: oggi(), controparteId: "", imponibile: "", aliquota: 22, contoEco: "", dataScadenza: "" });
    setAvviso(["ok", `Movimento n. ${prossimoNumero()} registrato: protocollo IVA ${c.registroIva} assegnato.`]);
  };

  const totMan = fMan.righe.reduce((a, r) => ({ d: r2(a.d + (+r.dare || 0)), av: r2(a.av + (+r.avere || 0)) }), { d: 0, av: 0 });
  const squadrato = r2(totMan.d - totMan.av);

  const registraManuale = () => {
    const righe = fMan.righe.filter((r) => r.conto && ((+r.dare || 0) !== 0 || (+r.avere || 0) !== 0))
      .map((r) => ({ conto: r.conto, dare: r2(+r.dare || 0), avere: r2(+r.avere || 0) }));
    if (righe.length < 2) { setAvviso(["ko", "Servono almeno due righe con conto e importo."]); return; }
    if (squadrato !== 0) { setAvviso(["ko", `Registrazione bloccata: sbilancio di ${fmtE(squadrato)}. Dare e avere devono coincidere.`]); return; }
    aggiungiMov({
      id: uid(), aziendaId: azId, numero: prossimoNumero(), data: fMan.data, causaleId: causale,
      descrizione: fMan.descrizione || CAUSALI.find((x) => x.id === causale).nome,
      stato: "registrata", righe, creatoIl: new Date().toISOString(), operatore: "studio",
    });
    setFMan({ data: oggi(), descrizione: "", righe: [{ conto: "", dare: "", avere: "" }, { conto: "", dare: "", avere: "" }] });
    setAvviso(["ok", "Movimento registrato a libro giornale."]);
  };

  const storna = (mov) => {
    const n = prossimoNumero();
    setDb((p) => ({
      ...p,
      movimenti: p.movimenti.map((m) => (m.id === mov.id ? { ...m, stato: "stornata" } : m)).concat([{
        id: uid(), aziendaId: azId, numero: n, data: oggi(), causaleId: "PN",
        descrizione: `Storno movimento n. ${mov.numero} — ${mov.descrizione}`, stato: "storno",
        righe: mov.righe.map((r) => ({ conto: r.conto, dare: r.avere, avere: r.dare })),
        creatoIl: new Date().toISOString(), operatore: "studio", stornoDi: mov.numero,
      }]),
    }));
    setAvviso(["warn", `Creato storno n. ${n}. Nota: per i documenti IVA la rettifica fiscale richiede nota di credito.`]);
  };

  const saldaScadenza = (s) => {
    const inc = s.tipo === "incasso";
    const n = prossimoNumero();
    setDb((p) => ({
      ...p,
      movimenti: p.movimenti.map((m) => (m.id === s.mov.id ? { ...m, scadenza: { ...m.scadenza, saldata: true } } : m)).concat([{
        id: uid(), aziendaId: azId, numero: n, data: oggi(), causaleId: inc ? "IN" : "PG",
        descrizione: `${inc ? "Incasso" : "Pagamento"} — ${s.mov.descrizione}`, stato: "registrata",
        righe: inc
          ? [{ conto: "01.02", dare: s.importo, avere: 0 }, { conto: "02.01", dare: 0, avere: s.importo }]
          : [{ conto: "10.01", dare: s.importo, avere: 0 }, { conto: "01.02", dare: 0, avere: s.importo }],
        creatoIl: new Date().toISOString(), operatore: "studio",
      }]),
    }));
    setAvviso(["ok", `${inc ? "Incasso" : "Pagamento"} registrato (mov. n. ${n}) su Banca c/c e partita chiusa.`]);
  };

  const registraLiquidazione = () => {
    if (!liq) return;
    const righe = [];
    if (liq.ivaDeb) righe.push({ conto: "10.02", dare: liq.ivaDeb, avere: 0 });
    if (liq.ivaCred) righe.push({ conto: "03.01", dare: 0, avere: liq.ivaCred });
    const credP = r2(+creditoPrec || 0);
    if (credP) righe.push({ conto: "02.05", dare: 0, avere: credP });
    if (liq.saldo > 0) righe.push({ conto: "10.03", dare: 0, avere: liq.saldo });
    else if (liq.saldo < 0) righe.push({ conto: "02.05", dare: -liq.saldo, avere: 0 });
    const nomePeriodo = liq.mensile ? MESI_N[periodoLiq] : `${periodoLiq + 1}° trimestre`;
    aggiungiMov({
      id: uid(), aziendaId: azId, numero: prossimoNumero(), data: oggi(), causaleId: "PN",
      descrizione: `Liquidazione IVA ${nomePeriodo} ${az.esercizio}`, stato: "registrata",
      righe, creatoIl: new Date().toISOString(), operatore: "studio",
    });
    setAvviso(["ok", liq.saldo > 0
      ? `Liquidazione registrata: IVA a debito ${fmtE(liq.saldo)} da versare con F24 (cod. tributo 60${String((liq.mensile ? periodoLiq + 1 : periodoLiq + 31)).padStart(2, "0")}) entro il giorno 16.`
      : `Liquidazione registrata: credito IVA di ${fmtE(-liq.saldo)} riportato a nuovo.`]);
  };

  const resetDemo = async () => {
    const d = datiDemo(); setDb(d); setAzId("az1");
    try { await window.storage.set("registro-contabilita:v1", JSON.stringify(d)); } catch {}
    setAvviso(["info", "Archivio ripristinato con i dati dimostrativi."]);
  };

  if (!db || !az) return <div style={{ fontFamily: "sans-serif", padding: 40, color: C.tenue }}>Apertura archivio…</div>;

  const NAV = [
    ["dashboard", "Cruscotto"], ["primanota", "Prima nota"], ["giornale", "Libro giornale"],
    ["mastrini", "Mastrini"], ["verifica", "Bilancio di verifica"], ["iva", "Registri IVA"],
    ["liquidazione", "Liquidazione IVA"], ["scadenzario", "Scadenzario"],
    ["piano", "Piano dei conti"], ["anagrafiche", "Anagrafiche"],
  ];

  const kpiBanca = saldi["01.02"] ? r2(saldi["01.02"].dare - saldi["01.02"].avere) : 0;
  const kpiCassa = saldi["01.01"] ? r2(saldi["01.01"].dare - saldi["01.01"].avere) : 0;
  const scadIncassi = r2(scadAperte.filter((s) => s.tipo === "incasso").reduce((a, s) => a + s.importo, 0));
  const scadPagamenti = r2(scadAperte.filter((s) => s.tipo === "pagamento").reduce((a, s) => a + s.importo, 0));
  const scadScadute = scadAperte.filter((s) => s.data < oggi());

  const causaleMeta = CAUSALI.find((x) => x.id === causale);
  const modoDoc = causale === "FV" || causale === "FA";

  return (
    <div className="app">
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Marcellus&family=Archivo:wght@400;500;600&family=Spline+Sans+Mono:wght@400;500&display=swap');
        *{box-sizing:border-box}
        .app{min-height:100vh;background:${C.carta};color:${C.inchiostro};font-family:'Archivo',system-ui,sans-serif;display:grid;grid-template-columns:225px 1fr}
        .rubrica{border-right:1px solid ${C.linea};position:sticky;top:0;height:100vh;display:flex;flex-direction:column;background:${C.carta}}
        .testata{padding:26px 22px 18px;border-bottom:1px solid ${C.linea}}
        .marchio{font-family:'Marcellus',serif;font-size:22px}
        .marchio-sub{font-family:'Spline Sans Mono',monospace;font-size:9.5px;letter-spacing:.24em;text-transform:uppercase;color:${C.tenue};margin-top:3px}
        .voce{display:flex;gap:11px;align-items:baseline;width:100%;text-align:left;padding:10px 22px;border:none;background:none;cursor:pointer;font-family:'Archivo';font-size:13.5px;color:${C.tenue};border-left:3px solid transparent}
        .voce:hover{color:${C.inchiostro};background:${C.cartaScura}55}
        .voce.attiva{color:${C.verde};border-left-color:${C.verde};font-weight:600;background:${C.verdeCh}55}
        .voce .lett{font-family:'Spline Sans Mono',monospace;font-size:9.5px}
        .stato-salv{margin-top:auto;padding:14px 22px;border-top:1px solid ${C.linea};font-family:'Spline Sans Mono',monospace;font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:${C.tenue}}
        .contenuto{padding:0 clamp(18px,4vw,52px) 72px;max-width:1240px;width:100%}
        .barra{display:flex;justify-content:space-between;align-items:center;gap:14px;flex-wrap:wrap;padding:18px 0;border-bottom:1px solid ${C.inchiostro};margin-bottom:30px}
        select,input{font-family:'Spline Sans Mono',monospace;font-size:13px;padding:8px 10px;border:1px solid ${C.linea};background:${C.bianco};color:${C.inchiostro};font-variant-numeric:tabular-nums}
        select:focus,input:focus,button:focus-visible{outline:2px solid ${C.verde};outline-offset:1px}
        .campo{display:flex;flex-direction:column;gap:4px}
        .campo>span{font-size:11.5px;color:${C.tenue}}
        .griglia{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:12px 16px}
        .pannello{background:${C.bianco};border:1px solid ${C.linea};padding:22px;margin-bottom:22px}
        .pannello h3{font-family:'Marcellus',serif;font-weight:400;font-size:19px;margin:0 0 14px}
        .kpi-gr{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:1px;background:${C.linea};border:1px solid ${C.linea};margin-bottom:22px}
        .kpi{background:${C.bianco};padding:16px 18px}
        .kpi b{display:block;font-family:'Spline Sans Mono',monospace;font-size:21px;font-weight:500;margin:7px 0 5px;font-variant-numeric:tabular-nums}
        .kpi small{font-family:'Spline Sans Mono',monospace;font-size:9.5px;letter-spacing:.16em;text-transform:uppercase;color:${C.tenue}}
        .kpi .det{font-size:11.5px;color:${C.tenue}}
        table.tab{width:100%;border-collapse:collapse;font-size:12.5px}
        .tab th{font-family:'Spline Sans Mono',monospace;font-size:9.5px;letter-spacing:.13em;text-transform:uppercase;color:${C.tenue};text-align:left;padding:9px 10px;border-bottom:1px solid ${C.inchiostro};white-space:nowrap}
        .tab td{padding:9px 10px;border-bottom:1px solid ${C.linea};font-variant-numeric:tabular-nums;vertical-align:top}
        .tab td.num,.tab th.num{text-align:right;font-family:'Spline Sans Mono',monospace}
        .tab tr.tot td{border-top:2px solid ${C.inchiostro};font-weight:600;font-family:'Spline Sans Mono',monospace}
        .btn{font-family:'Archivo';font-size:13px;font-weight:600;padding:10px 18px;border:1px solid ${C.verde};background:${C.verde};color:${C.bianco};cursor:pointer}
        .btn:disabled{opacity:.45;cursor:not-allowed}
        .btn.sec{background:transparent;color:${C.verde}}
        .btn.mini{padding:5px 10px;font-size:11.5px}
        .btn.rosso{border-color:${C.rosso};color:${C.rosso};background:transparent}
        .avviso{padding:12px 16px;border-left:3px solid;margin-bottom:20px;font-size:13px;background:${C.bianco}}
        .tabmodo{display:flex;gap:0;margin-bottom:16px;border:1px solid ${C.linea};width:fit-content}
        .tabmodo button{border:none;background:${C.bianco};padding:9px 16px;font-family:'Spline Sans Mono',monospace;font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:${C.tenue};cursor:pointer}
        .tabmodo button.on{background:${C.inchiostro};color:${C.bianco}}
        .nota{font-size:12px;color:${C.tenue};line-height:1.6;border-left:2px solid ${C.linea};padding-left:13px;margin-top:14px}
        .scroll{overflow-x:auto}
        @media(max-width:900px){
          .app{grid-template-columns:1fr}
          .rubrica{position:static;height:auto;flex-direction:row;overflow-x:auto;border-right:none;border-bottom:1px solid ${C.linea}}
          .testata,.stato-salv{display:none}
          .rubrica nav{display:flex}
          .voce{white-space:nowrap;border-left:none;border-bottom:3px solid transparent;padding:13px 14px}
          .voce.attiva{border-bottom-color:${C.verde}}
        }
      `}</style>

      {/* ---------- navigazione ---------- */}
      <aside className="rubrica">
        <div className="testata">
          <div className="marchio">Registro</div>
          <div className="marchio-sub">Contabilità di studio</div>
        </div>
        <nav style={{ paddingTop: 8 }}>
          {NAV.map(([id, nome], i) => (
            <button key={id} className={`voce ${sez === id ? "attiva" : ""}`} onClick={() => { setSez(id); setAvviso(null); }}>
              <span className="lett">{String.fromCharCode(65 + i)}</span>{nome}
            </button>
          ))}
        </nav>
        <div className="stato-salv">
          {salvataggio === "salvato" && "● Archivio salvato"}
          {salvataggio === "in-corso" && "○ Salvataggio…"}
          {salvataggio === "nuovo" && "● Archivio nuovo"}
          {salvataggio === "sessione" && "△ Solo sessione"}
        </div>
      </aside>

      <main className="contenuto">
        {/* ---------- barra azienda ---------- */}
        <div className="barra">
          <div style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
            <label className="campo">
              <span>Azienda in lavorazione</span>
              <select value={azId} onChange={(e) => setAzId(e.target.value)}>
                {db.aziende.map((a) => <option key={a.id} value={a.id}>{a.nome}</option>)}
              </select>
            </label>
            <div style={{ fontSize: 12, color: C.tenue }}>
              P.IVA {az.piva} · {az.regime} · IVA {az.periodicitaIva} · Esercizio {az.esercizio}
            </div>
          </div>
          <button className="btn sec mini" onClick={resetDemo}>Ripristina dati demo</button>
        </div>

        {avviso && (
          <div className="avviso" style={{ borderColor: { ok: C.verde, warn: C.ambra, ko: C.rosso, info: C.blu }[avviso[0]] }}>
            {avviso[1]}
          </div>
        )}

        {/* ================= CRUSCOTTO ================= */}
        {sez === "dashboard" && (
          <>
            <Eyebrow>Sezione A · {az.nome}</Eyebrow>
            <Titolo>Cruscotto operativo</Titolo>
            <Sotto>Lo stato della posizione del cliente a colpo d'occhio: liquidità, partite aperte, prossimi adempimenti e ultime registrazioni.</Sotto>

            <div className="kpi-gr">
              <div className="kpi"><small>Saldo Banca c/c</small><b>{fmtE(kpiBanca)}</b><span className="det">da mastrino 01.02</span></div>
              <div className="kpi"><small>Saldo Cassa</small><b>{fmtE(kpiCassa)}</b><span className="det">da mastrino 01.01</span></div>
              <div className="kpi"><small>Crediti da incassare</small><b>{fmtE(scadIncassi)}</b><span className="det">{scadAperte.filter((s) => s.tipo === "incasso").length} partite aperte</span></div>
              <div className="kpi"><small>Debiti da pagare</small><b>{fmtE(scadPagamenti)}</b><span className="det">{scadAperte.filter((s) => s.tipo === "pagamento").length} partite aperte</span></div>
              <div className="kpi"><small>Scadenze già scadute</small><b style={{ color: scadScadute.length ? C.rosso : C.verde }}>{scadScadute.length}</b><span className="det">{scadScadute.length ? "richiedono azione" : "nessuna in ritardo"}</span></div>
              <div className="kpi"><small>Movimenti registrati</small><b>{postati.length}</b><span className="det">esercizio {az.esercizio}</span></div>
            </div>

            <div className="pannello">
              <h3>Prossime scadenze</h3>
              <div className="scroll"><table className="tab">
                <thead><tr><th>Scadenza</th><th>Documento</th><th>Tipo</th><th className="num">Importo</th><th>Stato</th><th></th></tr></thead>
                <tbody>
                  {scadAperte.slice(0, 6).map((s) => (
                    <tr key={s.mov.id}>
                      <td style={{ fontFamily: "'Spline Sans Mono',monospace" }}>{fmtD(s.data)}</td>
                      <td>{s.mov.descrizione}</td>
                      <td><Pill tono={s.tipo === "incasso" ? "info" : "neutro"}>{s.tipo}</Pill></td>
                      <td className="num">{fmtE(s.importo)}</td>
                      <td>{s.data < oggi() ? <Pill tono="ko">Scaduta</Pill> : <Pill tono="warn">Aperta</Pill>}</td>
                      <td><button className="btn mini" onClick={() => saldaScadenza(s)}>{s.tipo === "incasso" ? "Incassa" : "Paga"}</button></td>
                    </tr>
                  ))}
                  {!scadAperte.length && <tr><td colSpan={6} style={{ color: C.tenue }}>Nessuna partita aperta: tutte le scadenze risultano saldate.</td></tr>}
                </tbody>
              </table></div>
            </div>

            <div className="pannello">
              <h3>Ultime registrazioni</h3>
              <div className="scroll"><table className="tab">
                <thead><tr><th className="num">N.</th><th>Data</th><th>Causale</th><th>Descrizione</th><th className="num">Importo</th><th>Stato</th></tr></thead>
                <tbody>
                  {[...postati].reverse().slice(0, 6).map((m) => (
                    <tr key={m.id}>
                      <td className="num">{m.numero}</td>
                      <td style={{ fontFamily: "'Spline Sans Mono',monospace" }}>{fmtD(m.data)}</td>
                      <td><Pill tono="neutro">{m.causaleId}</Pill></td>
                      <td>{m.descrizione}</td>
                      <td className="num">{fmtE(m.righe.reduce((a, r) => a + (+r.dare || 0), 0))}</td>
                      <td>{m.stato === "stornata" ? <Pill tono="ko">Stornata</Pill> : m.stato === "storno" ? <Pill tono="warn">Storno</Pill> : <Pill>Registrata</Pill>}</td>
                    </tr>
                  ))}
                </tbody>
              </table></div>
            </div>
          </>
        )}

        {/* ================= PRIMA NOTA ================= */}
        {sez === "primanota" && (
          <>
            <Eyebrow>Sezione B · Inserimento guidato</Eyebrow>
            <Titolo>Prima nota</Titolo>
            <Sotto>
              Scegli la causale: per le fatture bastano imponibile e aliquota — l'articolo in partita
              doppia, il protocollo IVA e la scadenza vengono generati in automatico. La registrazione
              manuale è bloccata finché dare e avere non quadrano.
            </Sotto>

            <div className="pannello">
              <div className="tabmodo">
                {CAUSALI.map((c) => (
                  <button key={c.id} className={causale === c.id ? "on" : ""} onClick={() => setCausale(c.id)}>{c.id} · {c.nome}</button>
                ))}
              </div>

              {modoDoc ? (
                <>
                  <div className="griglia">
                    <label className="campo"><span>Data registrazione</span>
                      <input type="date" value={fDoc.data} onChange={(e) => setFDoc({ ...fDoc, data: e.target.value })} /></label>
                    <label className="campo"><span>Numero documento</span>
                      <input value={fDoc.numDoc} onChange={(e) => setFDoc({ ...fDoc, numDoc: e.target.value })} placeholder="es. 14/2026" /></label>
                    <label className="campo"><span>Data documento</span>
                      <input type="date" value={fDoc.dataDoc} onChange={(e) => setFDoc({ ...fDoc, dataDoc: e.target.value })} /></label>
                    <label className="campo"><span>{causale === "FV" ? "Cliente" : "Fornitore"}</span>
                      <select value={fDoc.controparteId} onChange={(e) => setFDoc({ ...fDoc, controparteId: e.target.value })}>
                        <option value="">— seleziona —</option>
                        {cpDiAz.filter((c) => c.tipo === (causale === "FV" ? "cliente" : "fornitore")).map((c) => <option key={c.id} value={c.id}>{c.nome}</option>)}
                      </select></label>
                    <label className="campo"><span>{causale === "FV" ? "Conto di ricavo" : "Conto di costo"}</span>
                      <select value={fDoc.contoEco} onChange={(e) => setFDoc({ ...fDoc, contoEco: e.target.value })}>
                        <option value="">— seleziona —</option>
                        {conti.filter((c) => c.tipo === (causale === "FV" ? "CE-R" : "CE-C")).map((c) => <option key={c.codice} value={c.codice}>{c.codice} {c.nome}</option>)}
                      </select></label>
                    <label className="campo"><span>Imponibile €</span>
                      <input type="number" step="0.01" value={fDoc.imponibile} onChange={(e) => setFDoc({ ...fDoc, imponibile: e.target.value })} /></label>
                    <label className="campo"><span>Aliquota IVA</span>
                      <select value={fDoc.aliquota} onChange={(e) => setFDoc({ ...fDoc, aliquota: +e.target.value })}>
                        {ALIQUOTE.map((a) => <option key={a} value={a}>{a}%</option>)}
                      </select></label>
                    <label className="campo"><span>Scadenza {causale === "FV" ? "incasso" : "pagamento"}</span>
                      <input type="date" value={fDoc.dataScadenza} onChange={(e) => setFDoc({ ...fDoc, dataScadenza: e.target.value })} /></label>
                  </div>

                  {/* anteprima articolo */}
                  {(+fDoc.imponibile || 0) > 0 && (
                    <div style={{ marginTop: 18 }}>
                      <div style={{ fontFamily: "'Spline Sans Mono',monospace", fontSize: 10, letterSpacing: ".16em", textTransform: "uppercase", color: C.tenue, marginBottom: 8 }}>Anteprima articolo in partita doppia</div>
                      <div className="scroll"><table className="tab">
                        <thead><tr><th>Conto</th><th className="num">Dare</th><th className="num">Avere</th></tr></thead>
                        <tbody>
                          {(() => {
                            const imp = r2(+fDoc.imponibile), iva = r2(imp * fDoc.aliquota / 100), tot = r2(imp + iva);
                            const rr = causale === "FV"
                              ? [["02.01", tot, 0], [fDoc.contoEco || "— ricavo —", 0, imp], ...(iva ? [["10.02", 0, iva]] : [])]
                              : [[fDoc.contoEco || "— costo —", imp, 0], ...(iva ? [["03.01", iva, 0]] : []), ["10.01", 0, tot]];
                            return rr.map(([c, d, a], i) => (
                              <tr key={i}><td>{c} {contoNome(c) !== c ? "· " + contoNome(c) : ""}</td>
                                <td className="num">{d ? fmtE(d) : ""}</td><td className="num">{a ? fmtE(a) : ""}</td></tr>
                            ));
                          })()}
                        </tbody>
                      </table></div>
                    </div>
                  )}
                  <div style={{ marginTop: 18, display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
                    <button className="btn" onClick={registraDocumento}>Registra fattura</button>
                    <span style={{ fontSize: 12, color: C.tenue }}>Genera scrittura, riga nel registro IVA {causaleMeta.registroIva} e scadenza.</span>
                  </div>
                </>
              ) : (
                <>
                  <div className="griglia" style={{ marginBottom: 14 }}>
                    <label className="campo"><span>Data</span>
                      <input type="date" value={fMan.data} onChange={(e) => setFMan({ ...fMan, data: e.target.value })} /></label>
                    <label className="campo" style={{ gridColumn: "span 2" }}><span>Descrizione</span>
                      <input value={fMan.descrizione} onChange={(e) => setFMan({ ...fMan, descrizione: e.target.value })} placeholder="es. Giroconto cassa → banca" /></label>
                  </div>
                  <div className="scroll"><table className="tab">
                    <thead><tr><th style={{ width: "45%" }}>Conto</th><th className="num">Dare €</th><th className="num">Avere €</th><th></th></tr></thead>
                    <tbody>
                      {fMan.righe.map((r, i) => (
                        <tr key={i}>
                          <td><select style={{ width: "100%" }} value={r.conto}
                            onChange={(e) => setFMan({ ...fMan, righe: fMan.righe.map((x, j) => j === i ? { ...x, conto: e.target.value } : x) })}>
                            <option value="">— conto —</option>
                            {conti.map((c) => <option key={c.codice} value={c.codice}>{c.codice} {c.nome}</option>)}
                          </select></td>
                          <td className="num"><input type="number" step="0.01" style={{ width: 120, textAlign: "right" }} value={r.dare}
                            onChange={(e) => setFMan({ ...fMan, righe: fMan.righe.map((x, j) => j === i ? { ...x, dare: e.target.value } : x) })} /></td>
                          <td className="num"><input type="number" step="0.01" style={{ width: 120, textAlign: "right" }} value={r.avere}
                            onChange={(e) => setFMan({ ...fMan, righe: fMan.righe.map((x, j) => j === i ? { ...x, avere: e.target.value } : x) })} /></td>
                          <td>{fMan.righe.length > 2 && <button className="btn mini rosso" onClick={() => setFMan({ ...fMan, righe: fMan.righe.filter((_, j) => j !== i) })}>×</button>}</td>
                        </tr>
                      ))}
                      <tr className="tot">
                        <td>Totali</td>
                        <td className="num">{fmtE(totMan.d)}</td>
                        <td className="num">{fmtE(totMan.av)}</td>
                        <td></td>
                      </tr>
                    </tbody>
                  </table></div>
                  <div style={{ marginTop: 16, display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
                    <button className="btn sec mini" onClick={() => setFMan({ ...fMan, righe: [...fMan.righe, { conto: "", dare: "", avere: "" }] })}>+ Aggiungi riga</button>
                    <button className="btn" disabled={squadrato !== 0 || totMan.d === 0} onClick={registraManuale}>Registra movimento</button>
                    {squadrato !== 0
                      ? <Pill tono="ko">Sbilancio {fmtE(squadrato)}</Pill>
                      : totMan.d > 0 ? <Pill>Quadratura OK</Pill> : null}
                  </div>
                </>
              )}
            </div>
            <div className="nota">
              Regole applicate: quadratura dare/avere obbligatoria · numerazione progressiva automatica ·
              i movimenti registrati non sono eliminabili, solo stornabili dal libro giornale con scrittura
              inversa tracciata · protocolli IVA assegnati in sequenza per registro.
            </div>
          </>
        )}

        {/* ================= LIBRO GIORNALE ================= */}
        {sez === "giornale" && (
          <>
            <Eyebrow>Sezione C · Art. 2216 c.c.</Eyebrow>
            <Titolo>Libro giornale</Titolo>
            <Sotto>Tutte le operazioni in ordine cronologico con l'articolo completo. Lo storno crea la scrittura inversa e marca l'originale, senza mai cancellare.</Sotto>
            <div className="pannello"><div className="scroll">
              <table className="tab">
                <thead><tr><th className="num">N.</th><th>Data</th><th>Caus.</th><th>Descrizione / Conti</th><th className="num">Dare</th><th className="num">Avere</th><th>Stato</th><th></th></tr></thead>
                <tbody>
                  {postati.map((m) => (
                    m.righe.map((r, i) => (
                      <tr key={m.id + i} style={m.stato === "stornata" ? { opacity: .55 } : {}}>
                        {i === 0 && <>
                          <td className="num" rowSpan={m.righe.length}>{m.numero}</td>
                          <td rowSpan={m.righe.length} style={{ fontFamily: "'Spline Sans Mono',monospace" }}>{fmtD(m.data)}</td>
                          <td rowSpan={m.righe.length}><Pill tono="neutro">{m.causaleId}</Pill></td>
                        </>}
                        <td>{i === 0 && <div style={{ fontWeight: 600, marginBottom: 3 }}>{m.descrizione}</div>}
                          <span style={{ color: C.tenue }}>{r.conto}</span> {contoNome(r.conto)}</td>
                        <td className="num">{r.dare ? fmtE(r.dare) : ""}</td>
                        <td className="num">{r.avere ? fmtE(r.avere) : ""}</td>
                        {i === 0 && <>
                          <td rowSpan={m.righe.length}>
                            {m.stato === "stornata" ? <Pill tono="ko">Stornata</Pill> : m.stato === "storno" ? <Pill tono="warn">Storno n.{m.stornoDi}</Pill> : <Pill>Registrata</Pill>}
                          </td>
                          <td rowSpan={m.righe.length}>
                            {m.stato === "registrata" && <button className="btn mini rosso" onClick={() => storna(m)}>Storna</button>}
                          </td>
                        </>}
                      </tr>
                    ))
                  ))}
                </tbody>
              </table>
            </div></div>
          </>
        )}

        {/* ================= MASTRINI ================= */}
        {sez === "mastrini" && (
          <>
            <Eyebrow>Sezione D · Partitari</Eyebrow>
            <Titolo>Mastrini</Titolo>
            <Sotto>La scheda di ogni conto con saldo progressivo, per rispondere in un secondo a «quanto abbiamo in banca?» o «quanto ci deve quel cliente?».</Sotto>
            <div className="pannello">
              <label className="campo" style={{ maxWidth: 420, marginBottom: 18 }}>
                <span>Conto</span>
                <select value={contoMastro} onChange={(e) => setContoMastro(e.target.value)}>
                  {conti.map((c) => <option key={c.codice} value={c.codice}>{c.codice} · {c.nome}</option>)}
                </select>
              </label>
              <div className="scroll"><table className="tab">
                <thead><tr><th>Data</th><th className="num">Mov.</th><th>Descrizione</th><th className="num">Dare</th><th className="num">Avere</th><th className="num">Saldo</th></tr></thead>
                <tbody>
                  {(() => {
                    let saldo = 0; const righe = [];
                    postati.forEach((m) => m.righe.forEach((r) => {
                      if (r.conto !== contoMastro) return;
                      saldo = r2(saldo + (+r.dare || 0) - (+r.avere || 0));
                      righe.push(
                        <tr key={m.id + r.conto + saldo}>
                          <td style={{ fontFamily: "'Spline Sans Mono',monospace" }}>{fmtD(m.data)}</td>
                          <td className="num">{m.numero}</td><td>{m.descrizione}</td>
                          <td className="num">{r.dare ? fmtE(r.dare) : ""}</td>
                          <td className="num">{r.avere ? fmtE(r.avere) : ""}</td>
                          <td className="num" style={{ fontWeight: 600, color: saldo < 0 ? C.rosso : C.inchiostro }}>{fmtE(saldo)}</td>
                        </tr>
                      );
                    }));
                    return righe.length ? righe : <tr><td colSpan={6} style={{ color: C.tenue }}>Nessun movimento su questo conto nell'esercizio.</td></tr>;
                  })()}
                </tbody>
              </table></div>
            </div>
          </>
        )}

        {/* ================= BILANCIO DI VERIFICA ================= */}
        {sez === "verifica" && (
          <>
            <Eyebrow>Sezione E · Situazione contabile</Eyebrow>
            <Titolo>Bilancio di verifica</Titolo>
            <Sotto>Saldi di tutti i conti movimentati con controllo di quadratura generale. È il punto di partenza per assestamenti e bilancio d'esercizio.</Sotto>
            {["SP-A", "SP-P", "CE-C", "CE-R"].map((tipo) => {
              const righe = conti.filter((c) => saldi[c.codice] && (saldi[c.codice].dare || saldi[c.codice].avere)).filter((c) => c.tipo === tipo);
              if (!righe.length) return null;
              return (
                <div className="pannello" key={tipo}>
                  <h3>{TIPO_NOME[tipo]}</h3>
                  <div className="scroll"><table className="tab">
                    <thead><tr><th>Conto</th><th className="num">Tot. dare</th><th className="num">Tot. avere</th><th className="num">Saldo dare</th><th className="num">Saldo avere</th></tr></thead>
                    <tbody>
                      {righe.map((c) => {
                        const s = saldi[c.codice]; const diff = r2(s.dare - s.avere);
                        return (
                          <tr key={c.codice}>
                            <td><span style={{ color: C.tenue }}>{c.codice}</span> {c.nome}</td>
                            <td className="num">{fmtE(s.dare)}</td><td className="num">{fmtE(s.avere)}</td>
                            <td className="num">{diff > 0 ? fmtE(diff) : ""}</td>
                            <td className="num">{diff < 0 ? fmtE(-diff) : ""}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table></div>
                </div>
              );
            })}
            <div className="pannello">
              <h3>Quadratura generale</h3>
              {(() => {
                const tD = r2(Object.values(saldi).reduce((a, s) => a + s.dare, 0));
                const tA = r2(Object.values(saldi).reduce((a, s) => a + s.avere, 0));
                const ricavi = r2(conti.filter((c) => c.tipo === "CE-R").reduce((a, c) => a + (saldi[c.codice] ? saldi[c.codice].avere - saldi[c.codice].dare : 0), 0));
                const costi = r2(conti.filter((c) => c.tipo === "CE-C").reduce((a, c) => a + (saldi[c.codice] ? saldi[c.codice].dare - saldi[c.codice].avere : 0), 0));
                return (
                  <div className="scroll"><table className="tab"><tbody>
                    <tr><td>Totale dare</td><td className="num">{fmtE(tD)}</td></tr>
                    <tr><td>Totale avere</td><td className="num">{fmtE(tA)}</td></tr>
                    <tr className="tot"><td>Sbilancio</td><td className="num" style={{ color: tD === tA ? C.verde : C.rosso }}>{tD === tA ? "0,00 — quadrato ✓" : fmtE(r2(tD - tA))}</td></tr>
                    <tr><td>Risultato economico provvisorio (ricavi − costi)</td>
                      <td className="num" style={{ fontWeight: 600, color: ricavi - costi >= 0 ? C.verde : C.rosso }}>{fmtE(r2(ricavi - costi))}</td></tr>
                  </tbody></table></div>
                );
              })()}
            </div>
          </>
        )}

        {/* ================= REGISTRI IVA ================= */}
        {sez === "iva" && (
          <>
            <Eyebrow>Sezione F · D.P.R. 633/1972, artt. 23 e 25</Eyebrow>
            <Titolo>Registri IVA</Titolo>
            <Sotto>Fatture emesse e ricevute con protocollo progressivo, imponibile per aliquota e imposta. Le righe nascono da sole registrando le fatture in prima nota.</Sotto>
            <div className="tabmodo">
              <button className={regIvaVista === "vendite" ? "on" : ""} onClick={() => setRegIvaVista("vendite")}>Vendite (art. 23)</button>
              <button className={regIvaVista === "acquisti" ? "on" : ""} onClick={() => setRegIvaVista("acquisti")}>Acquisti (art. 25)</button>
            </div>
            <div className="pannello"><div className="scroll">
              <table className="tab">
                <thead><tr><th className="num">Prot.</th><th>Data reg.</th><th>Doc.</th><th>Data doc.</th><th>Controparte</th><th className="num">Imponibile</th><th className="num">Aliq.</th><th className="num">Imposta</th><th className="num">Totale</th></tr></thead>
                <tbody>
                  {righeIva(regIvaVista).map((m) => (
                    <tr key={m.id}>
                      <td className="num">{m.iva.protocollo}</td>
                      <td style={{ fontFamily: "'Spline Sans Mono',monospace" }}>{fmtD(m.data)}</td>
                      <td>{m.iva.numDoc}</td>
                      <td style={{ fontFamily: "'Spline Sans Mono',monospace" }}>{fmtD(m.iva.dataDoc)}</td>
                      <td>{cpNome(m.iva.controparteId)}</td>
                      <td className="num">{fmtE(m.iva.imponibile)}</td>
                      <td className="num">{m.iva.aliquota}%</td>
                      <td className="num">{fmtE(m.iva.imposta)}</td>
                      <td className="num">{fmtE(r2(m.iva.imponibile + m.iva.imposta))}</td>
                    </tr>
                  ))}
                  <tr className="tot">
                    <td colSpan={5}>Totali registro</td>
                    <td className="num">{fmtE(r2(righeIva(regIvaVista).reduce((a, m) => a + m.iva.imponibile, 0)))}</td>
                    <td></td>
                    <td className="num">{fmtE(r2(righeIva(regIvaVista).reduce((a, m) => a + m.iva.imposta, 0)))}</td>
                    <td className="num">{fmtE(r2(righeIva(regIvaVista).reduce((a, m) => a + m.iva.imponibile + m.iva.imposta, 0)))}</td>
                  </tr>
                </tbody>
              </table>
            </div></div>
          </>
        )}

        {/* ================= LIQUIDAZIONE ================= */}
        {sez === "liquidazione" && liq && (
          <>
            <Eyebrow>Sezione G · Periodicità {az.periodicitaIva}</Eyebrow>
            <Titolo>Liquidazione IVA</Titolo>
            <Sotto>Il saldo del periodo calcolato dai registri, con la scrittura di giroconto generabile in un clic e l'indicazione del versamento F24.</Sotto>
            <div className="pannello">
              <div style={{ display: "flex", gap: 14, alignItems: "flex-end", flexWrap: "wrap", marginBottom: 18 }}>
                <label className="campo"><span>Periodo</span>
                  <select value={periodoLiq} onChange={(e) => setPeriodoLiq(+e.target.value)}>
                    {liq.mensile
                      ? MESI_N.map((m, i) => <option key={i} value={i}>{m} {az.esercizio}</option>)
                      : [0, 1, 2, 3].map((t) => <option key={t} value={t}>{t + 1}° trimestre {az.esercizio}</option>)}
                  </select></label>
                <label className="campo"><span>Credito periodo precedente €</span>
                  <input type="number" step="0.01" value={creditoPrec} onChange={(e) => setCreditoPrec(e.target.value)} style={{ width: 150 }} /></label>
              </div>
              <div className="scroll"><table className="tab"><tbody>
                <tr><td>IVA sulle vendite (a debito) — {liq.vend.length} documenti</td><td className="num">{fmtE(liq.ivaDeb)}</td></tr>
                <tr><td>IVA sugli acquisti (detraibile) — {liq.acq.length} documenti</td><td className="num">− {fmtE(liq.ivaCred)}</td></tr>
                <tr><td>Credito riportato dal periodo precedente</td><td className="num">− {fmtE(+creditoPrec || 0)}</td></tr>
                <tr className="tot"><td>{liq.saldo >= 0 ? "IVA da versare" : "Credito IVA del periodo"}</td>
                  <td className="num" style={{ color: liq.saldo > 0 ? C.rosso : C.verde }}>{fmtE(Math.abs(liq.saldo))}</td></tr>
              </tbody></table></div>
              <div style={{ marginTop: 18, display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
                <button className="btn" onClick={registraLiquidazione} disabled={!liq.ivaDeb && !liq.ivaCred}>Genera scrittura di liquidazione</button>
                {liq.saldo > 0 && <span style={{ fontSize: 12.5, color: C.tenue }}>Versamento con F24 entro il giorno 16 del {liq.mensile ? "mese successivo" : "secondo mese successivo al trimestre"}.</span>}
              </div>
              <div className="nota">
                La scrittura chiude «IVA a debito» e «IVA a credito» del periodo e rileva il saldo su
                «Erario c/IVA» (se a debito) o «Crediti v/erario» (se a credito). La comunicazione LIPE
                trimestrale riprende questi stessi totali.
              </div>
            </div>
          </>
        )}

        {/* ================= SCADENZARIO ================= */}
        {sez === "scadenzario" && (
          <>
            <Eyebrow>Sezione H · Partite aperte</Eyebrow>
            <Titolo>Scadenzario</Titolo>
            <Sotto>Incassi e pagamenti attesi. Il pulsante di saldo genera automaticamente la scrittura su Banca c/c e chiude la partita.</Sotto>
            {["aperte", "saldate"].map((vista) => {
              const righe = scadenze.filter((s) => vista === "aperte" ? !s.saldata : s.saldata);
              return (
                <div className="pannello" key={vista}>
                  <h3>{vista === "aperte" ? `Partite aperte (${righe.length})` : `Partite saldate (${righe.length})`}</h3>
                  <div className="scroll"><table className="tab">
                    <thead><tr><th>Scadenza</th><th>Documento</th><th>Tipo</th><th className="num">Importo</th><th>Stato</th>{vista === "aperte" && <th></th>}</tr></thead>
                    <tbody>
                      {righe.map((s) => (
                        <tr key={s.mov.id}>
                          <td style={{ fontFamily: "'Spline Sans Mono',monospace" }}>{fmtD(s.data)}</td>
                          <td>{s.mov.descrizione}</td>
                          <td><Pill tono={s.tipo === "incasso" ? "info" : "neutro"}>{s.tipo}</Pill></td>
                          <td className="num">{fmtE(s.importo)}</td>
                          <td>{s.saldata ? <Pill>Saldata</Pill> : s.data < oggi() ? <Pill tono="ko">Scaduta {fmtD(s.data)}</Pill> : <Pill tono="warn">Aperta</Pill>}</td>
                          {vista === "aperte" && <td><button className="btn mini" onClick={() => saldaScadenza(s)}>{s.tipo === "incasso" ? "Registra incasso" : "Registra pagamento"}</button></td>}
                        </tr>
                      ))}
                      {!righe.length && <tr><td colSpan={6} style={{ color: C.tenue }}>Nessuna partita in questa vista.</td></tr>}
                    </tbody>
                  </table></div>
                </div>
              );
            })}
          </>
        )}

        {/* ================= PIANO DEI CONTI ================= */}
        {sez === "piano" && (
          <>
            <Eyebrow>Sezione I</Eyebrow>
            <Titolo>Piano dei conti</Titolo>
            <Sotto>Struttura base a sezioni (attivo, passivo, costi, ricavi) estendibile con conti personalizzati per l'azienda in lavorazione.</Sotto>
            {["SP-A", "SP-P", "CE-C", "CE-R"].map((tipo) => (
              <div className="pannello" key={tipo}>
                <h3>{TIPO_NOME[tipo]}</h3>
                <div className="scroll"><table className="tab">
                  <thead><tr><th style={{ width: 110 }}>Codice</th><th>Denominazione</th><th className="num">Movimenti</th></tr></thead>
                  <tbody>
                    {conti.filter((c) => c.tipo === tipo).map((c) => (
                      <tr key={c.codice}>
                        <td style={{ fontFamily: "'Spline Sans Mono',monospace" }}>{c.codice}</td>
                        <td>{c.nome}{c.aziendaId && <span style={{ color: C.tenue }}> · personalizzato</span>}</td>
                        <td className="num">{postati.reduce((n, m) => n + m.righe.filter((r) => r.conto === c.codice).length, 0)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table></div>
              </div>
            ))}
            <div className="pannello">
              <h3>Nuovo conto personalizzato</h3>
              <div className="griglia">
                <label className="campo"><span>Codice</span><input value={nuovoConto.codice} onChange={(e) => setNuovoConto({ ...nuovoConto, codice: e.target.value })} placeholder="es. 20.09" /></label>
                <label className="campo"><span>Denominazione</span><input value={nuovoConto.nome} onChange={(e) => setNuovoConto({ ...nuovoConto, nome: e.target.value })} /></label>
                <label className="campo"><span>Sezione</span>
                  <select value={nuovoConto.tipo} onChange={(e) => setNuovoConto({ ...nuovoConto, tipo: e.target.value })}>
                    {Object.entries(TIPO_NOME).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                  </select></label>
              </div>
              <button className="btn" style={{ marginTop: 14 }} disabled={!nuovoConto.codice || !nuovoConto.nome || conti.some((c) => c.codice === nuovoConto.codice)}
                onClick={() => { setDb((p) => ({ ...p, contiExtra: [...p.contiExtra, { ...nuovoConto, aziendaId: azId }] })); setNuovoConto({ codice: "", nome: "", tipo: "CE-C" }); setAvviso(["ok", "Conto aggiunto al piano dei conti."]); }}>
                Aggiungi conto
              </button>
            </div>
          </>
        )}

        {/* ================= ANAGRAFICHE ================= */}
        {sez === "anagrafiche" && (
          <>
            <Eyebrow>Sezione L · Multi-azienda</Eyebrow>
            <Titolo>Anagrafiche</Titolo>
            <Sotto>Le aziende gestite dallo studio e la rubrica clienti/fornitori dell'azienda in lavorazione.</Sotto>
            <div className="pannello">
              <h3>Aziende dello studio</h3>
              <div className="scroll"><table className="tab">
                <thead><tr><th>Ragione sociale</th><th>P.IVA</th><th>Regime</th><th>IVA</th><th>Esercizio</th><th className="num">Movimenti</th></tr></thead>
                <tbody>
                  {db.aziende.map((a) => (
                    <tr key={a.id} style={a.id === azId ? { background: C.verdeCh + "44" } : {}}>
                      <td style={{ fontWeight: a.id === azId ? 600 : 400 }}>{a.nome}</td>
                      <td style={{ fontFamily: "'Spline Sans Mono',monospace" }}>{a.piva}</td>
                      <td>{a.regime}</td><td>{a.periodicitaIva}</td><td>{a.esercizio}</td>
                      <td className="num">{db.movimenti.filter((m) => m.aziendaId === a.id).length}</td>
                    </tr>
                  ))}
                </tbody>
              </table></div>
            </div>
            <div className="pannello">
              <h3>Rubrica clienti e fornitori — {az.nome}</h3>
              <div className="scroll"><table className="tab">
                <thead><tr><th>Denominazione</th><th>P.IVA</th><th>Tipo</th></tr></thead>
                <tbody>
                  {cpDiAz.map((c) => (
                    <tr key={c.id}><td>{c.nome}</td>
                      <td style={{ fontFamily: "'Spline Sans Mono',monospace" }}>{c.piva}</td>
                      <td><Pill tono={c.tipo === "cliente" ? "info" : "neutro"}>{c.tipo}</Pill></td></tr>
                  ))}
                </tbody>
              </table></div>
              <div className="griglia" style={{ marginTop: 18 }}>
                <label className="campo"><span>Denominazione</span><input value={nuovaCp.nome} onChange={(e) => setNuovaCp({ ...nuovaCp, nome: e.target.value })} /></label>
                <label className="campo"><span>Partita IVA</span><input value={nuovaCp.piva} onChange={(e) => setNuovaCp({ ...nuovaCp, piva: e.target.value })} /></label>
                <label className="campo"><span>Tipo</span>
                  <select value={nuovaCp.tipo} onChange={(e) => setNuovaCp({ ...nuovaCp, tipo: e.target.value })}>
                    <option value="cliente">Cliente</option><option value="fornitore">Fornitore</option>
                  </select></label>
              </div>
              <button className="btn" style={{ marginTop: 14 }} disabled={!nuovaCp.nome}
                onClick={() => { setDb((p) => ({ ...p, controparti: [...p.controparti, { ...nuovaCp, id: uid(), aziendaId: azId }] })); setNuovaCp({ nome: "", piva: "", tipo: "cliente" }); setAvviso(["ok", "Anagrafica aggiunta alla rubrica."]); }}>
                Aggiungi alla rubrica
              </button>
            </div>
          </>
        )}
      </main>
    </div>
  );
}
