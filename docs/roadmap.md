# Registro Contabilità — Roadmap di Sviluppo

> Roadmap v1.0 — 2026-07-02
> Sei fasi incrementali. Ogni fase termina con software funzionante, testato e demo-abile alla titolare dello studio. Convenzioni: percorsi backend relativi a `backend/src/`, frontend a `frontend/src/`. Ogni modulo consegna sempre: schema dati + migrazione Alembic + service layer + endpoint API v1 + validazioni server-side + test + seed italiani (definizione di modulo "completo").

**Regola trasversale di "done" (vale per ogni fase):**
- CI verde: `ruff` + `mypy --strict` + `pytest` (coverage ≥ 80% sui service) + `eslint` + `tsc` + build Next.js
- Migrazioni applicabili da zero (`alembic upgrade head` su DB vuoto) e reversibili di un passo
- Nessun endpoint privo di controllo permessi; nessuna query fuori RLS
- Audit log presente per ogni azione di scrittura introdotta nella fase
- Demo end-to-end su ambiente Docker Compose con dati seed

---

## Fase 1 — Fondazioni (setup, auth, multi-tenant, anagrafiche, piano dei conti, audit)

**Obiettivo**: piattaforma sicura e multi-tenant su cui ogni fase successiva monta solo logica di dominio. Alla fine, la commercialista può creare aziende clienti, gestire collaboratori e consultare il piano dei conti.

**Deliverable verificabili**
1. Monorepo `backend/` + `frontend/` + `infra/`; `docker compose up` porta su DB, Redis, MinIO, API, worker, web, mailpit; `make dev` esegue migrazioni + seed.
2. CI GitHub Actions (lint, typecheck, test, build immagini) su ogni PR.
3. Auth JWT: login, refresh rotante, logout con revoca, hash argon2id, rate-limit sul login.
4. Multi-tenancy: RLS attiva su ogni tabella tenant-scoped, middleware `SET LOCAL app.tenant_id`, ruoli PG `app_user`/`app_migrator` separati.
5. RBAC: ruoli seed (`owner`, `accountant`, `collaborator`, `viewer`), permessi `<ctx>.<azione>`, guard FastAPI `require_permission()`.
6. CRUD `ClientEntity` con validazione P.IVA (check-digit) e CF; assegnazione collaboratori (`user_client_access`).
7. CRUD `Party` (clienti/fornitori) con creazione automatica del partitario L4.
8. Piano dei conti: seed del piano standard italiano (§10 domain-model), clonazione template per nuova azienda, CRUD conti custom (solo foglie, no delete se movimentato — predisposto).
9. Audit log: `AuditRecorder` + tabella partizionata mensile + endpoint di consultazione filtrabile (solo `owner`).
10. Frontend: login, shell applicativa (selettore azienda cliente), pagine anagrafiche e piano dei conti; client TS generato da OpenAPI in CI.

**Moduli/file principali**
```
backend/src/shared/{tenancy.py, security.py, audit.py, money.py, errors.py, events.py}
backend/src/studio/{models,schemas,services/{auth,users,roles,audit},api/v1,seeds,tests}
backend/src/parties/{models,schemas,services/{client_entities,parties,accounts},api/v1,seeds,tests}
backend/migrations/versions/000{1..4}_*.py
infra/{docker-compose.yml, Dockerfile.api, Dockerfile.web, init-db/01-roles.sql}
.github/workflows/{ci.yml}
frontend/src/app/{(auth)/login, (app)/clients, (app)/parties, (app)/chart-of-accounts}
frontend/src/lib/api/ (client generato)
```

**Test richiesti**
- Unit: check-digit P.IVA/CF, hashing/verifica password, generazione codici partitario.
- Integrazione (pytest + Postgres reale): **test di isolamento tenant** — due tenant seed, ogni endpoint invocato cross-tenant deve dare 404/0 righe; test che una query senza `SET LOCAL` non restituisce righe (RLS FORCE).
- Integrazione: permessi — `collaborator` non può gestire utenti; utente senza `user_client_access` non vede l'azienda.
- Integrazione: ogni scrittura produce riga audit con before/after corretti.
- E2E (Playwright): login → crea azienda → clona piano conti → crea fornitore → verifica partitario.

**Done quando**: regola trasversale + i test di isolamento tenant passano + demo: creare seconda azienda cliente e un collaboratore che vede solo quella.

---

## Fase 2 — Core contabile (prima nota, causali, giornale, mastrini, bilancio di verifica, IVA base, scadenzario)

**Obiettivo**: lo studio può tenere la contabilità ordinaria quotidiana di un'azienda cliente reale, in parallelo al vecchio gestionale (shadow run).

**Deliverable verificabili**
1. `FiscalYear`: CRUD, vincolo di non sovrapposizione, stato `open`.
2. Causali seed (FV, NCV, FA, NCA, FAP, INC, PAG, STO, LIB, GIR) con template di riga; motore `EntryComposer` che dai ruoli genera le righe proposte.
3. Prima nota: creazione draft (anche squadrata), modifica draft, **posting transazionale** con: quadratura server-side, assegnazione `journal_number` da `sequence_counter` FOR UPDATE, verifica esercizio aperto, immutabilità post-posting (service + trigger di guardia).
4. Storno: scrittura inversa collegata, mai DELETE su posted.
5. Registri IVA acquisti/vendite: `VatEntry` protocollata nella stessa transazione del posting per causali IVA; righe per aliquota con seed `vat_rate` (22, 10, 5, 4, N1–N7); stampa PDF registro per periodo.
6. Libro giornale: query cronologica per esercizio + stampa PDF conforme (numero riga, data, numero giornale, conto, descrizione, dare, avere).
7. Mastrini/partitari: estratto conto per conto e per soggetto con saldo progressivo; drill-down dalla riga al dettaglio scrittura.
8. Bilancio di verifica: per periodo arbitrario, ricalcolato da `journal_line` (non dalla cache), con totale dare = totale avere garantito; export CSV/PDF.
9. Scadenzario: generazione rate al posting fattura (termini di pagamento del soggetto), viste "in scadenza/scadute", chiusura rate da causali INC/PAG (anche parziale), riapertura su storno.
10. Worker: ricalcolo `account_balance` su eventi posted/reversed.
11. Frontend: griglia prima nota con inserimento da tastiera (tab/invio), form guidati per causale, libro giornale, mastrini, bilancio di verifica, registri IVA, scadenzario con badge scadute.

**Moduli/file principali**
```
backend/src/accounting/{domain/{entry.py,invariants.py},models,schemas,
    services/{fiscal_years,templates,journal(post/reverse),ledger,trial_balance,schedules},
    api/v1,seeds/templates_seed.py,tests}
backend/src/tax/{models,schemas,services/{vat_registers,vat_entries},api/v1,seeds/vat_rates.py,tests}
backend/src/shared/pdf/{journal_book.py, vat_register.py} + templates HTML
backend/migrations/versions/000{5..9}_*.py (incl. partizioni journal_entry/vat_entry + trigger)
frontend/src/app/(app)/{journal, ledger, trial-balance, vat-registers, schedules, fiscal-years}
```

**Test richiesti**
- Unit dominio (senza DB): quadratura, composizione causali (FV/FA/FAP con ritenuta), calcolo IVA per aliquota con arrotondamenti (property-based con Hypothesis: per qualsiasi insieme di righe generate, posted ⇒ bilanciata).
- Integrazione: posting concorrente — 20 posting paralleli sulla stessa azienda ⇒ numeri giornale consecutivi senza buchi né duplicati (idem protocolli IVA).
- Integrazione: storno riapre rate scadenzario; doppio storno rifiutato; posting su esercizio inesistente/data fuori range rifiutato.
- Integrazione: UPDATE/DELETE diretto su entry posted bloccato dal trigger.
- Report: bilancio di verifica su dataset seed noto = valori attesi golden-file; PDF giornale contiene tutte le scritture in ordine.
- E2E: ciclo completo fattura vendita → incasso parziale → incasso saldo → mastrino cliente a zero.

**Done quando**: regola trasversale + un mese di contabilità reale di un'azienda pilota inserito in shadow run con quadratura identica al gestionale attuale (bilancio di verifica confrontato).

---

## Fase 3 — Fiscalità (liquidazione IVA, ritenute, F24, calendario adempimenti)

**Obiettivo**: gli adempimenti IVA periodici e le ritenute escono dal sistema senza calcoli a mano.

**Deliverable verificabili**
1. Liquidazione IVA mensile/trimestrale: raccolta `VatEntry` non liquidate del periodo, calcolo debito/credito con detraibilità parziale, riporto credito precedente, interessi 1% per trimestrali, gestione acconto di dicembre; stato draft → confirmed; alla conferma: giroconto automatico (causale LIQ) + assegnazione `vat_settlement_id` alle entry + immutabilità.
2. Vincolo di sequenzialità liquidazioni; prospetto di liquidazione PDF; riepilogo annuale (base per dichiarazione IVA).
3. Ritenute d'acconto passive: generate dalla causale FAP, scadenza al 16 del mese successivo, stato accrued → paid; riepilogo per certificazione (base CU).
4. F24: modello draft da liquidazione IVA (6001–6012, 6031–6034) e ritenute (1040), compensazione con crediti disponibili, marcatura pagato ⇒ scrittura PAGF24 proposta.
5. Calendario adempimenti per azienda: scadenze generate automaticamente (liquidazioni 16/mese, F24, acconto IVA 27/12) + scadenze manuali; vista studio cross-azienda ("cosa scade questa settimana su tutti i clienti"); notifiche email via worker.
6. Frontend: wizard liquidazione con anteprima e conferma, pagina F24, calendario adempimenti studio e per azienda.

**Moduli/file principali**
```
backend/src/tax/services/{vat_settlement.py, withholdings.py, f24.py, deadlines.py}
backend/src/tax/domain/{settlement_calc.py}          # calcolo puro, testabile senza DB
backend/src/tax/api/v1/{settlements.py, f24.py, deadlines.py}
backend/src/shared/pdf/{vat_settlement.py, f24_draft.py}
backend/workers/{deadline_notifier.py}
backend/migrations/versions/00{10..12}_*.py
frontend/src/app/(app)/{vat-settlements, f24, deadlines}
```

**Test richiesti**
- Unit `settlement_calc`: casi golden — debito semplice; credito riportato; trimestrale con interessi 1%; acconto dicembre; detraibilità 40% (auto promiscue); nota credito che rende il periodo a credito.
- Integrazione: conferma liquidazione = transazione unica (giroconto + congelamento entry + audit); tentativo di stornare fattura già liquidata ⇒ rettifica nel periodo corrente, la liquidazione passata non cambia.
- Integrazione: liquidazione periodo N rifiutata se N−1 non confermata; doppia conferma rifiutata.
- Integrazione: F24 con compensazione non può andare sotto zero per sezione.
- E2E: trimestre completo con fatture miste → liquidazione → F24 → pagamento → conti erariali a saldo atteso.

**Done quando**: regola trasversale + le liquidazioni di un trimestre reale dell'azienda pilota coincidono al centesimo con quelle prodotte dal gestionale attuale.

---

## Fase 4 — Bilancio e cespiti (ammortamenti, assestamento, chiusura/riapertura)

**Obiettivo**: chiudere un esercizio dentro il sistema: dalle scritture di assestamento al bilancio, alla riapertura.

**Deliverable verificabili**
1. Registro cespiti: entità `Asset`, `AssetCategory` (coefficienti ministeriali seed), `DepreciationPlan`; acquisizione da fattura di acquisto, dismissione/vendita con plus/minusvalenza.
2. Ammortamenti: piano civilistico per cespite, generazione scritture di ammortamento annuali (o mensili per bilanci infra-annuali) in bozza, con riduzione al 50% del coefficiente per il primo esercizio; stampa registro cespiti.
3. Scritture di assestamento guidate: ratei/risconti (con calcolo pro-rata temporis da periodo di competenza), fatture da emettere/ricevere, rimanenze finali, TFR, fondo svalutazione crediti; ogni assistente genera bozze da confermare.
4. Chiusura esercizio: procedura guidata — checklist (liquidazioni confermate, draft assenti o eliminate, assestamenti registrati) → epilogo conti economici a 5.1.01 → rilevazione utile/perdita a 2.1.05 → chiusura patrimoniali a 5.1.02 → `fiscal_year.status='closed'` (tutto transazionale, reversibile finché non si conferma).
5. Riapertura: generazione automatica bilancio di apertura del nuovo esercizio (causale APE) + riapertura risconti/fatture da ricevere; riapertura eccezionale di un esercizio chiuso solo con permesso dedicato + audit.
6. Bilancio d'esercizio: riclassificato civilistico abbreviato (art. 2435-bis) tramite mappatura `account.cee_code`; situazione economico-patrimoniale a data arbitraria; export PDF/CSV.
7. Blocco retroattivo: qualunque posting/storno/liquidazione con data in esercizio `closed` rifiutato ovunque (verifica cross-modulo).

**Moduli/file principali**
```
backend/src/accounting/services/{assets.py, depreciation.py, adjustments.py, year_end.py}
backend/src/accounting/domain/{depreciation_calc.py, accrual_calc.py}
backend/src/accounting/api/v1/{assets.py, year_end.py, financial_statements.py}
backend/src/parties/ (aggiunta cee_code su account + migrazione mappatura)
backend/src/shared/pdf/{asset_register.py, financial_statement.py}
backend/migrations/versions/00{13..16}_*.py
frontend/src/app/(app)/{assets, year-end (wizard), financial-statements}
```

**Test richiesti**
- Unit: piani di ammortamento (primo anno 50%, ultimo anno residuo, dismissione infrannuale con plus/minus), ratei/risconti pro-rata su periodi a cavallo.
- Integrazione: chiusura con draft pendenti rifiutata; chiusura+riapertura ⇒ bilancio apertura = patrimoniale di chiusura, conti economici a zero; dopo chiusura ogni scrittura datata nell'esercizio rifiutata (anche via API tax).
- Property-based: per qualsiasi esercizio seed, dopo l'epilogo la somma dei saldi di tutti i conti = 0.
- E2E: wizard chiusura completo sull'azienda pilota (esercizio precedente ricostruito).

**Done quando**: regola trasversale + chiusura dell'esercizio dell'azienda pilota con utile identico a quello del bilancio depositato.

---

## Fase 5 — Studio professionale (dashboard, pratiche, portale cliente)

**Obiettivo**: dal motore contabile allo strumento di lavoro dello studio: visione d'insieme, organizzazione del lavoro, canale col cliente.

**Deliverable verificabili**
1. Dashboard studio: stato contabilità per azienda (ultima registrazione, draft pendenti, prossimi adempimenti, liquidazioni da confermare), carico di lavoro per collaboratore, scadenze aggregate.
2. Task/pratiche: entità `Task` (titolo, azienda, assegnatario, scadenza, stato, checklist), generazione automatica di task dagli adempimenti fiscali (Fase 3), commenti interni; notifiche in-app ed email.
3. Portale cliente (nuovo ruolo `client_user`, accesso limitato alla propria `ClientEntity`): consultazione documenti e scadenzario, upload fatture/documenti verso lo studio (finisce in `documents.status='to_register'`), messaggistica essenziale con lo studio; superficie API separata `/api/v1/portal/*` con rate limiting e permessi ridotti hard-coded.
4. Report periodici per il cliente: situazione economica sintetica trimestrale PDF inviabile dal portale.
5. Hardening: revisione permessi per il nuovo attore esterno, 2FA obbligatoria per utenti studio, penetration test interno sul portale.

**Moduli/file principali**
```
backend/src/studio/services/{dashboard.py, tasks.py, notifications.py}
backend/src/studio/api/v1/{dashboard.py, tasks.py}
backend/src/portal/{api/v1, services, tests}      # bounded context nuovo, superficie minima
backend/src/documents/services/{uploads.py}
backend/migrations/versions/00{17..19}_*.py
frontend/src/app/(app)/{dashboard, tasks}
frontend/src/app/(portal)/…                        # layout e auth separati
```

**Test richiesti**
- Integrazione: `client_user` non può invocare NESSUN endpoint non-portal (test esaustivo generato dall'elenco route); non vede altre aziende; upload limitato per tipo/dimensione con verifica antivirus (clamav in compose).
- Integrazione: generazione automatica task da calendario adempimenti; chiusura task al completamento adempimento.
- E2E: cliente carica fattura dal portale → appare allo studio in "da registrare" → registrata con FA → sparisce dal portale come pendente.

**Done quando**: regola trasversale + un cliente pilota reale usa il portale per un mese senza incidenti di permessi (audit review).

---

## Fase 6 — Automazione (OCR fatture, riconciliazione bancaria, suggerimenti)

**Obiettivo**: ridurre il data-entry, che è il costo principale dello studio. Tutto ciò che è automatico produce **bozze**, mai posting diretti: l'ultima parola resta all'operatore.

**Deliverable verificabili**
1. Import FatturaPA XML: parsing del tracciato SDI (fattura singola e lotto), creazione `Document` + bozza di registrazione precompilata (anagrafica matchata su P.IVA, righe IVA per aliquota dal XML, conto proposto); gestione note credito e bollo.
2. OCR fatture cartacee/PDF: implementazione dell'interfaccia `DocumentExtractor` (Fase 1) con motore locale (tesseract/paddle) o servizio esterno configurabile; estrazione campi chiave con confidence score; sotto soglia ⇒ campo evidenziato da verificare.
3. Riconciliazione bancaria: import estratto conto (CSV/CAMT.053), motore di matching movimenti ↔ rate scadenzario e ↔ scritture (regole: importo+data±tolleranza, riferimento fattura, anagrafica); conferma manuale genera INC/PAG in bozza; movimenti non matchati ⇒ suggerimento causale.
4. Suggerimenti automatici: proposta conto di costo/ricavo per fornitore/cliente basata sullo storico delle registrazioni (frequenza per party, fallback su default_account_id); apprendimento incrementale semplice e spiegabile (niente black-box: si mostra il perché).
5. Metriche di automazione: % bozze accettate senza modifiche, tempo medio di registrazione — per dimostrare il ROI alla titolare.

**Moduli/file principali**
```
backend/src/documents/services/{fatturapa_import.py, ocr/, extraction.py}
backend/src/accounting/services/{bank_reconciliation.py, suggestions.py}
backend/src/accounting/domain/{matching_rules.py}    # regole pure, testabili
backend/workers/{ocr_worker.py, import_worker.py}
backend/migrations/versions/00{20..22}_*.py (bank_statement, bank_movement, suggestion_stats)
frontend/src/app/(app)/{inbox (documenti da registrare), reconciliation}
```

**Test richiesti**
- Unit: parser FatturaPA su corpus di XML reali anonimizzati (fattura semplice, multi-aliquota, nota credito, split payment, bollo); ogni campo estratto = atteso.
- Unit matching: golden set di estratti conto con esiti attesi (match esatto, parziale, ambiguo ⇒ nessun auto-match); property: mai match automatico con differenza importo > tolleranza.
- Integrazione: bozza da import non è mai posted automaticamente; rifiuto import duplicato (sha256/sdi_id).
- E2E: XML caricato → bozza FA precompilata → operatore conferma → protocollo IVA e scadenzario corretti.

**Done quando**: regola trasversale + su un mese di fatture reali dell'azienda pilota ≥ 70% delle bozze accettate senza modifiche e riconciliazione bancaria con ≥ 80% di match automatici corretti (zero falsi match confermati).

---

## Dipendenze tra fasi e rischi principali

```
F1 ──▶ F2 ──▶ F3 ──▶ F4 ──▶ F5 ──▶ F6
        │             ▲       (F5 e F6 parzialmente parallelizzabili
        └── documents └───────  dopo F3, su moduli disgiunti)
```

| Rischio | Mitigazione |
|---|---|
| Errori di calcolo fiscale | Calcoli in moduli puri con golden test; shadow run contro gestionale attuale (F2, F3) |
| Buchi di numerazione sotto concorrenza | Test di concorrenza dedicati in F2, counter FOR UPDATE, UNIQUE constraint |
| Leak cross-tenant col portale (F5) | RLS dal giorno 1, superficie portal separata, test esaustivo route |
| Migrazione dal vecchio gestionale | Da pianificare come attività trasversale (import saldi apertura + anagrafiche) — vedi Revisioni |

---

## Revisioni necessarie

Domande aperte per il titolare del progetto:

1. **Ordine di valore**: la priorità dello studio è ridurre il data-entry (anticipare import FatturaPA della Fase 6 subito dopo la Fase 2?) o arrivare presto agli adempimenti (Fase 3)? L'import XML è candidabile ad anticipo perché indipendente dalla riconciliazione.
2. **Azienda pilota**: quale cliente usare per lo shadow run di Fase 2/3? Serve un'azienda in ordinaria, con volumi medi e IVA trimestrale o mensile?
3. **Migrazione dati**: quando si migra dal gestionale attuale — solo saldi di apertura + anagrafiche (consigliato), o anche lo storico scritture? Con quale formato di export disponibile?
4. **Tempi e capacità**: quante persone/giorni a settimana sul progetto? Le fasi non hanno date volutamente: vanno calate sulla capacità reale.
5. **F24 telematico**: in Fase 3 l'F24 è un prospetto; serve l'export nel tracciato per Entratel/home banking (CBI) o basta il PDF da ricopiare?
6. **Portale cliente**: è davvero richiesto dai clienti dello studio o la Fase 5 può ridursi a dashboard+task interni? (taglio di scope significativo).
7. **OCR**: preferenza per motore locale (nessun dato fuori dallo studio, qualità inferiore) o servizio cloud (qualità superiore, valutazione GDPR/DPA necessaria)?
8. **Criteri di accettazione fiscali**: chi valida i golden test fiscali (liquidazioni, ammortamenti)? Proposta: la titolare firma i casi di test attesi prima dell'implementazione di F3/F4.
