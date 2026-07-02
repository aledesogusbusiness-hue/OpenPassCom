# Registro Contabilità — Modello di Dominio

> Documento di dominio v1.0 — 2026-07-02
> Convenzioni: PK sempre `id UUID DEFAULT gen_random_uuid()`. Colonne di audit standard su ogni tabella tenant-scoped: `tenant_id UUID NOT NULL`, `created_by UUID NOT NULL`, `updated_by UUID NOT NULL`, `created_at TIMESTAMPTZ NOT NULL DEFAULT now()`, `updated_at TIMESTAMPTZ NOT NULL DEFAULT now()` — indicate come **[std]** e non ripetute. Gli importi sono `NUMERIC(15,2)`, le aliquote `NUMERIC(5,2)`. Le date contabili sono `DATE` (la competenza è un giorno, non un istante); i timestamp tecnici `TIMESTAMPTZ`.

---

## 1. Contesto `studio` — tenant, sicurezza, audit

### 1.1 `Studio` (tenant root)

| Colonna | Tipo | Vincoli / note |
|---|---|---|
| id | UUID | PK — è il `tenant_id` di tutto il sistema |
| name | VARCHAR(200) | NOT NULL — ragione sociale studio |
| vat_number | CHAR(11) | NULL, CHECK cifra di controllo P.IVA |
| tax_code | VARCHAR(16) | NULL — CF studio |
| email | VARCHAR(254) | NOT NULL |
| pec | VARCHAR(254) | NULL |
| address, city, province, postal_code | VARCHAR(200), VARCHAR(100), CHAR(2), CHAR(5) | NULL |
| settings | JSONB | NOT NULL DEFAULT '{}' — preferenze studio |
| is_active | BOOLEAN | NOT NULL DEFAULT true |
| created_at / updated_at | TIMESTAMPTZ | NOT NULL DEFAULT now() |

Unica tabella senza `tenant_id` (è il tenant). Nessuna policy RLS di isolamento inter-riga: l'accesso è filtrato dal claim JWT.

### 1.2 `User` (`app_user`)

| Colonna | Tipo | Vincoli |
|---|---|---|
| id | UUID | PK |
| tenant_id | UUID | NOT NULL FK → studio(id) |
| email | VARCHAR(254) | NOT NULL, UNIQUE (tenant_id, lower(email)) |
| password_hash | VARCHAR(255) | NOT NULL — argon2id |
| first_name / last_name | VARCHAR(100) | NOT NULL |
| is_active | BOOLEAN | NOT NULL DEFAULT true |
| is_owner | BOOLEAN | NOT NULL DEFAULT false — titolare studio |
| last_login_at | TIMESTAMPTZ | NULL |
| mfa_secret | VARCHAR(255) | NULL — TOTP, cifrato at-rest |
| [std created/updated] | | created_by nullable solo per il primo utente (bootstrap) |

### 1.3 `Role`, `Permission`, `RolePermission`, `UserRole`

```sql
role            (id UUID PK, tenant_id UUID NOT NULL, code VARCHAR(50) NOT NULL,
                 name VARCHAR(100) NOT NULL, is_system BOOLEAN NOT NULL DEFAULT false,
                 UNIQUE (tenant_id, code))
permission      (id UUID PK, code VARCHAR(100) NOT NULL UNIQUE,      -- globale, seed
                 description VARCHAR(255) NOT NULL)                   -- es. 'journal.post'
role_permission (role_id UUID FK, permission_id UUID FK, PK (role_id, permission_id))
user_role       (user_id UUID FK, role_id UUID FK, PK (user_id, role_id))
```

Ruoli di sistema (seed): `owner` (tutto), `accountant` (contabilità completa, no gestione utenti), `collaborator` (prima nota draft, no posting, no chiusure), `viewer` (sola lettura). Permessi con formato `<contesto>.<azione>`: `journal.create`, `journal.post`, `journal.reverse`, `fiscal_year.close`, `vat.settle`, `users.manage`, `audit.read`, …

### 1.4 `UserClientAccess` — assegnazione collaboratore ↔ azienda cliente

```sql
user_client_access (user_id UUID FK app_user, client_entity_id UUID FK client_entity,
                    tenant_id UUID NOT NULL, granted_by UUID NOT NULL,
                    granted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    PK (user_id, client_entity_id))
```

Se un utente non ha righe qui e non è `owner`/`accountant`, non vede alcuna azienda.

### 1.5 `AuditLog` (append-only, partizionata per mese su `occurred_at`)

| Colonna | Tipo | Vincoli |
|---|---|---|
| id | UUID | PK (con occurred_at nella partition key) |
| tenant_id | UUID | NOT NULL |
| client_entity_id | UUID | NULL — se l'azione è scoped su azienda |
| occurred_at | TIMESTAMPTZ | NOT NULL DEFAULT now() |
| actor_id | UUID | NULL — NULL per azioni di sistema/worker |
| actor_label | VARCHAR(200) | NOT NULL — snapshot "Nome Cognome (email)" |
| action | VARCHAR(100) | NOT NULL — es. 'journal_entry.posted' |
| entity_type | VARCHAR(100) | NOT NULL — es. 'journal_entry' |
| entity_id | UUID | NULL |
| before | JSONB | NULL — stato precedente (solo campi cambiati) |
| after | JSONB | NULL — stato successivo |
| request_id | UUID | NULL |
| ip_address | INET | NULL |
| user_agent | VARCHAR(400) | NULL |

`REVOKE UPDATE, DELETE ON audit_log FROM app_user;`

### 1.6 `SequenceCounter` — numerazioni senza buchi

```sql
sequence_counter (tenant_id UUID NOT NULL, client_entity_id UUID NOT NULL,
                  scope VARCHAR(30) NOT NULL,   -- 'journal' | 'vat_purchases' | 'vat_sales' | ...
                  year SMALLINT NOT NULL,
                  last_value INTEGER NOT NULL DEFAULT 0,
                  PK (tenant_id, client_entity_id, scope, year))
```

Incremento solo con `SELECT ... FOR UPDATE` dentro la transazione di posting.

---

## 2. Contesto `parties` — aziende, anagrafiche, piano dei conti

### 2.1 `ClientEntity` (azienda cliente dello studio)

| Colonna | Tipo | Vincoli |
|---|---|---|
| id | UUID | PK |
| name | VARCHAR(200) | NOT NULL — ragione sociale |
| legal_form | VARCHAR(10) | NOT NULL — 'SRL','SPA','SNC','SAS','DI' (ditta individuale), 'SS', 'ALTRO' |
| vat_number | CHAR(11) | NULL, CHECK check-digit; UNIQUE (tenant_id, vat_number) |
| tax_code | VARCHAR(16) | NOT NULL — CF (16 alfanumerico o 11 numerico) |
| sdi_code | CHAR(7) | NULL — codice destinatario SDI |
| pec | VARCHAR(254) | NULL |
| address, city, province, postal_code, country_code | …, CHAR(2), CHAR(5), CHAR(2) DEFAULT 'IT' | |
| accounting_regime | VARCHAR(20) | NOT NULL — 'ordinaria' \| 'semplificata' \| 'forfettario' |
| vat_period | VARCHAR(10) | NOT NULL — 'monthly' \| 'quarterly' — periodicità liquidazione |
| vat_quarterly_interest | BOOLEAN | NOT NULL DEFAULT true — interessi 1% (trimestrale per opzione) |
| account_plan_id | UUID | NOT NULL FK → account_plan(id) |
| is_active | BOOLEAN | NOT NULL DEFAULT true |
| [std] | | |

### 2.2 `Party` (cliente/fornitore dell'azienda cliente)

| Colonna | Tipo | Vincoli |
|---|---|---|
| id | UUID | PK |
| client_entity_id | UUID | NOT NULL FK → client_entity(id) |
| kind | VARCHAR(10) | NOT NULL CHECK IN ('customer','supplier','both') |
| name | VARCHAR(200) | NOT NULL |
| vat_number | CHAR(11) | NULL |
| tax_code | VARCHAR(16) | NULL — CHECK: almeno uno tra vat_number e tax_code se country 'IT' |
| sdi_code | CHAR(7) | NULL |
| pec | VARCHAR(254) | NULL |
| address, city, province, postal_code, country_code | | |
| payment_terms_days | SMALLINT | NOT NULL DEFAULT 30 — gg fine mese/data fattura |
| payment_terms_end_of_month | BOOLEAN | NOT NULL DEFAULT false |
| default_account_id | UUID | NULL FK → account(id) — conto di costo/ricavo abituale |
| subaccount_id | UUID | NULL FK → account(id) — partitario dedicato (auto-creato) |
| withholding_subject | BOOLEAN | NOT NULL DEFAULT false — soggetto a ritenuta (professionisti) |
| notes | TEXT | NULL |
| is_active | BOOLEAN | NOT NULL DEFAULT true |
| [std] | | UNIQUE (client_entity_id, vat_number) parziale WHERE vat_number IS NOT NULL |

### 2.3 `AccountPlan`, `AccountType`, `Account`

```sql
account_plan (id UUID PK, tenant_id, name VARCHAR(100) NOT NULL,
              is_template BOOLEAN NOT NULL DEFAULT false,   -- il piano standard seed
              cloned_from_id UUID NULL FK account_plan(id), [std])

account_type (id SMALLSERIAL PK, code VARCHAR(20) UNIQUE NOT NULL, name VARCHAR(100),
              section VARCHAR(20) NOT NULL CHECK IN
                ('asset','liability','equity','revenue','expense','memorandum'),
              normal_side CHAR(1) NOT NULL CHECK IN ('D','A'))  -- lookup globale, seed
```

`Account` (conto):

| Colonna | Tipo | Vincoli |
|---|---|---|
| id | UUID | PK |
| account_plan_id | UUID | NOT NULL FK → account_plan(id) |
| parent_id | UUID | NULL FK → account(id) — gerarchia livelli 1→4 |
| code | VARCHAR(20) | NOT NULL — es. '1.2.01.001'; UNIQUE (account_plan_id, code) |
| name | VARCHAR(200) | NOT NULL |
| level | SMALLINT | NOT NULL CHECK BETWEEN 1 AND 4 |
| account_type_id | SMALLINT | NOT NULL FK → account_type(id) |
| is_postable | BOOLEAN | NOT NULL — TRUE solo per foglie (liv. 3–4) |
| is_vat_account | BOOLEAN | NOT NULL DEFAULT false |
| is_subaccount_parent | BOOLEAN | NOT NULL DEFAULT false — mastro clienti/fornitori che genera partitari |
| party_id | UUID | NULL FK → party(id) — valorizzato solo sui partitari auto-generati |
| is_active | BOOLEAN | NOT NULL DEFAULT true |
| [std] | | CHECK (is_postable = false OR level >= 3); CHECK ((party_id IS NULL) OR is_postable) |

---

## 3. Contesto `accounting` — esercizi, prima nota, causali

### 3.1 `FiscalYear` (esercizio contabile)

| Colonna | Tipo | Vincoli |
|---|---|---|
| id | UUID | PK |
| client_entity_id | UUID | NOT NULL FK |
| year_label | VARCHAR(9) | NOT NULL — '2026' o '2025/2026'; UNIQUE (client_entity_id, year_label) |
| start_date / end_date | DATE | NOT NULL, CHECK (end_date > start_date); EXCLUDE con daterange per non sovrapporre esercizi della stessa azienda |
| status | VARCHAR(12) | NOT NULL DEFAULT 'open' CHECK IN ('open','closing','closed') |
| closed_at | TIMESTAMPTZ | NULL |
| closed_by | UUID | NULL FK app_user |
| [std] | | |

### 3.2 `EntryTemplate` (causale contabile) e `EntryTemplateLine`

| `entry_template` | Tipo | Vincoli |
|---|---|---|
| id | UUID | PK |
| client_entity_id | UUID | NULL — NULL = causale standard di sistema (seed), altrimenti personalizzata |
| code | VARCHAR(10) | NOT NULL — 'FV','FA','INC','PAG','LIB',… UNIQUE (COALESCE(client_entity_id), code) |
| name | VARCHAR(100) | NOT NULL |
| behavior | VARCHAR(30) | NOT NULL CHECK IN ('sale_invoice','purchase_invoice','collection','payment','free','reversal','vat_settlement','opening','closing') |
| requires_party | BOOLEAN | NOT NULL |
| requires_document | BOOLEAN | NOT NULL — data/numero documento obbligatori |
| vat_register_kind | VARCHAR(15) | NULL CHECK IN ('sales','purchases') — se genera protocollo IVA |
| generates_schedule | BOOLEAN | NOT NULL DEFAULT false — crea rate a scadenzario |
| is_active | BOOLEAN | NOT NULL DEFAULT true |
| [std] | | |

```sql
entry_template_line (id UUID PK, entry_template_id UUID FK, line_order SMALLINT NOT NULL,
    side CHAR(1) NOT NULL CHECK IN ('D','A'),
    account_role VARCHAR(30) NOT NULL,  -- 'party_subaccount' | 'vat' | 'revenue' | 'expense'
                                        -- | 'cash_bank' | 'withholding' | 'fixed:<account_code>'
    amount_role  VARCHAR(20) NOT NULL)  -- 'total' | 'taxable' | 'vat' | 'net_to_pay' | 'withholding'
```

La causale è un *template guidato*: la UI chiede (anagrafica, imponibile, aliquota, conto ricavo/costo) e il service compone le righe secondo i ruoli. Il risultato è comunque una normale `JournalEntry` verificata dalle stesse invarianti.

### 3.3 `JournalEntry` (registrazione prima nota) — partizionata RANGE per anno su `entry_date`

| Colonna | Tipo | Vincoli |
|---|---|---|
| id | UUID | PK (id, entry_date) |
| client_entity_id | UUID | NOT NULL FK |
| fiscal_year_id | UUID | NOT NULL FK → fiscal_year(id) |
| entry_date | DATE | NOT NULL — data di registrazione/competenza; CHECK dentro l'esercizio (service) |
| journal_number | INTEGER | NULL — assegnato SOLO al posting; UNIQUE parziale (tenant_id, client_entity_id, fiscal_year_id, journal_number) WHERE journal_number IS NOT NULL |
| status | VARCHAR(10) | NOT NULL DEFAULT 'draft' CHECK IN ('draft','posted','reversed') |
| entry_template_id | UUID | NULL FK — causale usata |
| description | VARCHAR(500) | NOT NULL |
| document_date | DATE | NULL — obbligatoria se causale.requires_document |
| document_number | VARCHAR(50) | NULL — idem |
| party_id | UUID | NULL FK → party(id) |
| posted_at | TIMESTAMPTZ | NULL; posted_by UUID NULL |
| reversed_at | TIMESTAMPTZ | NULL; reversed_by UUID NULL |
| reversal_of_entry_id | UUID | NULL FK → journal_entry(id) — la scrittura di storno punta all'originale |
| vat_entry_id | UUID | NULL FK → vat_entry(id) — link al protocollo generato |
| [std] | | CHECK ((status='posted') = (journal_number IS NOT NULL AND posted_at IS NOT NULL)) |

### 3.4 `JournalLine` (riga dare/avere) — co-partizionata con la testata

| Colonna | Tipo | Vincoli |
|---|---|---|
| id | UUID | PK (id, entry_date) |
| journal_entry_id | UUID | NOT NULL FK (composito con entry_date) |
| entry_date | DATE | NOT NULL — denormalizzata per il partitioning |
| line_order | SMALLINT | NOT NULL — ordine di presentazione |
| account_id | UUID | NOT NULL FK → account(id), deve essere is_postable |
| side | CHAR(1) | NOT NULL CHECK IN ('D','A') |
| amount | NUMERIC(15,2) | NOT NULL CHECK (amount > 0) |
| description | VARCHAR(255) | NULL — default = descrizione testata |
| party_id | UUID | NULL — ridondato dal partitario per query veloci |
| [std tenant/client/audit] | | |

### 3.5 `AccountBalance` (saldi materializzati — cache, ricostruibile)

```sql
account_balance (tenant_id, client_entity_id, fiscal_year_id, account_id,
                 period CHAR(7) NOT NULL,           -- 'YYYY-MM'
                 debit_total NUMERIC(15,2) NOT NULL DEFAULT 0,
                 credit_total NUMERIC(15,2) NOT NULL DEFAULT 0,
                 updated_at TIMESTAMPTZ NOT NULL,
                 PK (tenant_id, client_entity_id, fiscal_year_id, account_id, period))
```

Aggiornata dal worker su evento `journal_entry.posted/reversed`; la fonte di verità resta sempre `journal_line` (il bilancio di verifica ufficiale ricalcola dalle righe).

---

## 4. Contesto `tax` — IVA, liquidazioni, ritenute

### 4.1 `VatRate` (lookup aliquote e nature, seed nazionale)

```sql
vat_rate (id SMALLSERIAL PK, code VARCHAR(10) UNIQUE NOT NULL, -- '22','10','5','4','N1'..'N7'
          rate NUMERIC(5,2) NOT NULL,                          -- 22.00, 0.00 per nature
          nature_code VARCHAR(4) NULL,   -- N1 escluse art.15, N2 non soggette, N3 non imponibili,
                                         -- N4 esenti, N5 margine, N6 reverse charge, N7 IVA UE
          description VARCHAR(200) NOT NULL,
          is_active BOOLEAN NOT NULL DEFAULT true,
          valid_from DATE NOT NULL, valid_to DATE NULL)
```

### 4.2 `VatRegister` (registro IVA per azienda)

```sql
vat_register (id UUID PK, client_entity_id UUID NOT NULL FK,
              kind VARCHAR(15) NOT NULL CHECK IN ('sales','purchases','corrispettivi'),
              name VARCHAR(100) NOT NULL,   -- 'Registro IVA vendite sez. 1'
              section SMALLINT NOT NULL DEFAULT 1,   -- sezionali
              UNIQUE (client_entity_id, kind, section), [std])
```

### 4.3 `VatEntry` (protocollo IVA) — partizionata RANGE annuale su `registration_date`

| Colonna | Tipo | Vincoli |
|---|---|---|
| id | UUID | PK (id, registration_date) |
| client_entity_id | UUID | NOT NULL |
| vat_register_id | UUID | NOT NULL FK |
| protocol_number | INTEGER | NOT NULL — da sequence_counter; UNIQUE (tenant_id, vat_register_id, protocol_year, protocol_number) |
| protocol_year | SMALLINT | NOT NULL |
| registration_date | DATE | NOT NULL |
| document_date | DATE | NOT NULL |
| document_number | VARCHAR(50) | NOT NULL |
| party_id | UUID | NOT NULL FK → party(id) |
| journal_entry_id | UUID | NOT NULL — FK logica alla scrittura che l'ha generata |
| total_amount | NUMERIC(15,2) | NOT NULL — totale documento |
| vat_settlement_id | UUID | NULL FK → vat_settlement(id) — valorizzato quando liquidata |
| is_deferred | BOOLEAN | NOT NULL DEFAULT false — IVA a esigibilità differita / split payment |
| status | VARCHAR(10) | NOT NULL DEFAULT 'posted' CHECK IN ('posted','reversed') |
| [std] | | |

### 4.4 `VatEntryLine` (riga per aliquota)

```sql
vat_entry_line (id UUID PK, vat_entry_id UUID FK (composito), registration_date DATE,
    vat_rate_id SMALLINT NOT NULL FK vat_rate,
    taxable_amount NUMERIC(15,2) NOT NULL,     -- imponibile (può essere negativa su NC)
    vat_amount NUMERIC(15,2) NOT NULL,         -- imposta; CHECK coerenza col rate (±0.01 per arrotondamento)
    deductible_percent NUMERIC(5,2) NOT NULL DEFAULT 100.00,  -- indetraibilità (acquisti)
    [std tenant/client/audit])
```

### 4.5 `VatSettlement` (liquidazione periodica)

| Colonna | Tipo | Vincoli |
|---|---|---|
| id | UUID | PK |
| client_entity_id | UUID | NOT NULL |
| year | SMALLINT | NOT NULL |
| period | SMALLINT | NOT NULL — mese 1–12 o trimestre 1–4 secondo periodicità |
| period_kind | VARCHAR(10) | NOT NULL CHECK IN ('monthly','quarterly'); UNIQUE (client_entity_id, year, period_kind, period) |
| vat_on_sales | NUMERIC(15,2) | NOT NULL — IVA a debito del periodo |
| vat_on_purchases | NUMERIC(15,2) | NOT NULL — IVA detraibile del periodo |
| prior_credit | NUMERIC(15,2) | NOT NULL DEFAULT 0 — credito periodo precedente |
| interest | NUMERIC(15,2) | NOT NULL DEFAULT 0 — 1% trimestrali |
| advance_paid | NUMERIC(15,2) | NOT NULL DEFAULT 0 — acconto dicembre |
| balance | NUMERIC(15,2) | NOT NULL — >0 debito, <0 credito da riportare |
| status | VARCHAR(10) | NOT NULL DEFAULT 'draft' CHECK IN ('draft','confirmed') |
| confirmed_at TIMESTAMPTZ, confirmed_by UUID | | NULL |
| journal_entry_id | UUID | NULL — scrittura di giroconto IVA generata alla conferma |
| f24_id | UUID | NULL FK → f24_model(id) |
| [std] | | |

### 4.6 `WithholdingEntry` (ritenute d'acconto) e `F24Model`

```sql
withholding_entry (id UUID PK, client_entity_id, journal_entry_id UUID NOT NULL,
    party_id UUID NOT NULL, kind VARCHAR(10) NOT NULL CHECK IN ('active','passive'),
    base_amount NUMERIC(15,2) NOT NULL, rate NUMERIC(5,2) NOT NULL DEFAULT 20.00,
    amount NUMERIC(15,2) NOT NULL, tax_code VARCHAR(10) NOT NULL DEFAULT '1040', -- codice tributo
    payment_due_date DATE NOT NULL,           -- 16 del mese successivo
    status VARCHAR(10) NOT NULL DEFAULT 'accrued' CHECK IN ('accrued','paid','certified'),
    [std])

f24_model (id UUID PK, client_entity_id, due_date DATE NOT NULL,
    status VARCHAR(10) NOT NULL DEFAULT 'draft' CHECK IN ('draft','ready','paid'),
    total_debit NUMERIC(15,2) NOT NULL, total_credit NUMERIC(15,2) NOT NULL,
    lines JSONB NOT NULL,   -- [{sezione, codice_tributo, rateazione, anno, debito, credito}]
    paid_at DATE NULL, [std])
```

---

## 5. Scadenzario (contesto `accounting`)

### 5.1 `PaymentSchedule` (piano scadenze di un documento)

```sql
payment_schedule (id UUID PK, client_entity_id UUID NOT NULL,
    journal_entry_id UUID NOT NULL,       -- la fattura registrata che lo origina
    party_id UUID NOT NULL,
    direction VARCHAR(10) NOT NULL CHECK IN ('inflow','outflow'),  -- incasso | pagamento
    total_amount NUMERIC(15,2) NOT NULL CHECK (total_amount > 0),
    [std])
```

### 5.2 `ScheduledPayment` (singola rata)

| Colonna | Tipo | Vincoli |
|---|---|---|
| id | UUID | PK |
| payment_schedule_id | UUID | NOT NULL FK |
| installment_no | SMALLINT | NOT NULL — UNIQUE (payment_schedule_id, installment_no) |
| due_date | DATE | NOT NULL |
| amount | NUMERIC(15,2) | NOT NULL CHECK (amount > 0) |
| settled_amount | NUMERIC(15,2) | NOT NULL DEFAULT 0 CHECK (settled_amount <= amount) — incassi parziali |
| status | VARCHAR(10) | NOT NULL DEFAULT 'open' CHECK IN ('open','partial','settled','cancelled') |
| settlement_entry_id | UUID | NULL — scrittura di incasso/pagamento che l'ha chiusa (ultima) |
| payment_method | VARCHAR(20) | NULL — 'bank_transfer','riba','cash','sdd','card' |
| notes | VARCHAR(255) | NULL |
| [std] | | |

Collegamento con la prima nota: la causale `collection`/`payment` chiede quali rate chiudere; il service aggiorna `settled_amount`/`status` nella stessa transazione del posting. Lo storno dell'incasso riapre le rate.

---

## 6. Contesto `documents`

```sql
document (id UUID PK, client_entity_id, kind VARCHAR(20) NOT NULL
              CHECK IN ('sale_invoice','purchase_invoice','credit_note','receipt','other'),
          direction VARCHAR(10) CHECK IN ('inbound','outbound'),
          party_id UUID NULL, document_date DATE, document_number VARCHAR(50),
          total_amount NUMERIC(15,2) NULL,
          status VARCHAR(15) NOT NULL DEFAULT 'to_register' CHECK IN ('to_register','registered','ignored'),
          sdi_id VARCHAR(50) NULL,          -- identificativo SDI per XML FatturaPA
          [std])

document_attachment (id UUID PK, document_id UUID FK, file_name VARCHAR(255),
          mime_type VARCHAR(100), byte_size BIGINT, storage_key VARCHAR(500) NOT NULL,
          sha256 CHAR(64) NOT NULL, [std])

document_entry_link (document_id UUID, journal_entry_id UUID, PK (document_id, journal_entry_id))
```

---

## 7. Relazioni principali (cardinalità)

```
Studio 1──N User            Studio 1──N ClientEntity        Studio 1──N Role
User   N──M Role            User N──M ClientEntity (user_client_access)
ClientEntity 1──N FiscalYear        ClientEntity N──1 AccountPlan
AccountPlan 1──N Account            Account N──1 Account (parent, albero ≤4 livelli)
Account N──1 AccountType            Party N──1 ClientEntity
Party 1──0..1 Account (partitario auto-generato)
FiscalYear 1──N JournalEntry        JournalEntry 1──N(≥2 se posted) JournalLine
JournalLine N──1 Account (postable) JournalEntry N──0..1 EntryTemplate (causale)
JournalEntry 0..1──0..1 JournalEntry (reversal_of_entry_id, storno)
JournalEntry 1──0..1 VatEntry       VatEntry N──1 VatRegister
VatEntry 1──N VatEntryLine          VatEntryLine N──1 VatRate
VatSettlement 1──N VatEntry (assegnazione al periodo liquidato)
JournalEntry 1──0..1 PaymentSchedule
PaymentSchedule 1──N ScheduledPayment
Document N──M JournalEntry (document_entry_link)
AuditLog N──1 Studio (nessuna FK dura verso le entità: sopravvive al dato)
```

Nota tecnica: le FK verso tabelle partizionate (`journal_entry`, `vat_entry`) sono composite (`id, entry_date`) oppure "FK logiche" validate dal service layer dove PostgreSQL non le supporta attraverso partizioni; la coerenza è coperta da test.

---

## 8. Invarianti di dominio

Verificate nel service layer (fail = 422 con codice errore) e, dove indicato ⚙, anche da constraint/trigger DB.

**Partita doppia e ciclo di vita**
1. ⚙ Per ogni `JournalEntry` con `status='posted'`: `SUM(righe D) = SUM(righe A)` e numero righe ≥ 2. Le draft possono essere squadrate, ma il posting le rifiuta.
2. ⚙ Ogni `JournalLine.amount > 0`; il segno è espresso solo da `side`.
3. ⚙ Una entry `posted` è immutabile (testata e righe). Unico UPDATE ammesso: `status → 'reversed'` + campi di storno.
4. Lo storno crea una nuova entry con righe a lati invertiti, importi identici, `reversal_of_entry_id` valorizzato, causale `reversal`; una entry è stornabile una sola volta.
5. La DELETE fisica è consentita solo su `status='draft'` (e comunque tracciata in audit).
6. `entry_date` ∈ [`fiscal_year.start_date`, `end_date`] e `fiscal_year.status='open'` al momento del posting E dello storno.
7. ⚙ `journal_number` esiste ⇔ status ∈ ('posted','reversed'); progressivo per (azienda, esercizio) senza buchi: `MAX(journal_number) = COUNT(*)` delle entry numerate — verificato da test di proprietà e da report di quadratura.
8. `JournalLine.account_id` deve puntare a un conto `is_postable=true`, attivo, del piano dei conti dell'azienda della entry.
9. Se la causale `requires_party`, `party_id` NOT NULL e ogni riga con `account_role='party_subaccount'` usa il partitario di quel soggetto.

**IVA**
10. Posting di causale con `vat_register_kind` ⇒ creazione `VatEntry` nella stessa transazione; il protocollo è progressivo senza buchi per (registro, anno).
11. ⚙ Per ogni `VatEntryLine`: `|vat_amount − round(taxable_amount × rate/100, 2)| ≤ 0.01` (tolleranza da arrotondamento documento); nature N* ⇒ `vat_amount = 0`.
12. La somma di imponibili+imposta delle righe = `total_amount` del documento (± ritenuta/bollo gestiti come righe fuori campo).
13. Una `VatEntry` entra in una e una sola `VatSettlement`; una settlement `confirmed` è immutabile e congela le sue VatEntry; lo storno di una fattura già liquidata non modifica la liquidazione passata ma genera rettifica nel periodo corrente.
14. Le liquidazioni di un anno vanno confermate in ordine di periodo; `prior_credit` del periodo N = `−balance` (se credito) della liquidazione N−1 confermata.

**Esercizi e chiusura**
15. `fiscal_year.status='closed'` ⇒ nessun posting/storno/liquidazione con data nell'esercizio; riapertura solo con permesso `fiscal_year.reopen` + audit.
16. Gli esercizi della stessa azienda non si sovrappongono (⚙ EXCLUDE constraint).

**Scadenzario**
17. ⚙ `SUM(scheduled_payment.amount) = payment_schedule.total_amount` (constraint trigger deferred).
18. `settled_amount ≤ amount`; `status` derivato: 0=open, parziale=partial, pieno=settled.
19. Lo storno della scrittura di incasso/pagamento ripristina `settled_amount` delle rate collegate.

**Trasversali**
20. Ogni tabella tenant-scoped: RLS attiva; `tenant_id` mai accettato dal client (deriva dal JWT).
21. Ogni transizione di stato (post, reverse, close, confirm) scrive `audit_log` nella stessa transazione.
22. Tutti gli importi transitano come `Decimal`/`NUMERIC`; serializzazione JSON come stringa (`"1234.56"`).

---

## 9. Causali standard (seed)

Legenda conti: vedi piano dei conti §10. `[P]` = partitario del soggetto.

| Code | Nome | Behavior | Righe generate (D=dare, A=avere) | Registro IVA | Scadenzario |
|---|---|---|---|---|---|
| **FV** | Fattura di vendita | sale_invoice | D `[P]` cliente (1.2.01.xxx) totale · A ricavo (4.1.xx) imponibile · A IVA vendite (2.4.02) imposta | vendite | sì (inflow) |
| **NCV** | Nota credito emessa | sale_invoice (negativa) | righe FV a lati invertiti | vendite (segno −) | riduce rate aperte |
| **FA** | Fattura di acquisto | purchase_invoice | D costo (3.x.xx) imponibile · D IVA acquisti (1.4.02) imposta · A `[P]` fornitore (2.2.01.xxx) totale | acquisti | sì (outflow) |
| **NCA** | Nota credito ricevuta | purchase_invoice (negativa) | righe FA invertite | acquisti (segno −) | riduce rate |
| **FAP** | Fattura professionista con r.a. | purchase_invoice | D costo (3.2.05) imponibile · D IVA acquisti (1.4.02) · A Erario c/ritenute (2.4.05) ritenuta · A `[P]` fornitore netto | acquisti | sì (netto) + WithholdingEntry |
| **INC** | Incasso da cliente | collection | D banca (1.1.02) o cassa (1.1.01) · A `[P]` cliente | — | chiude rate inflow |
| **PAG** | Pagamento a fornitore | payment | D `[P]` fornitore · A banca/cassa | — | chiude rate outflow |
| **LIQ** | Giroconto liquidazione IVA | vat_settlement | D IVA vendite (2.4.02) · A IVA acquisti (1.4.02) · sbilancio → A Erario c/IVA (2.4.03) se debito / D Credito IVA (1.4.03) se credito | — | debito → scadenza F24 |
| **PAGF24** | Pagamento F24 | payment | D Erario c/IVA / c/ritenute · A banca | — | chiude scadenza |
| **STO** | Storno | reversal | righe dell'originale a lati invertiti | eventuale rettifica | riapre rate |
| **APE** | Apertura esercizio | opening | riprende saldi patrimoniali da bilancio chiusura | — | — |
| **CHI** | Chiusura esercizio | closing | epiloga economici a 5.1.01, rileva utile/perdita a 2.1.05 | — | — |
| **LIB** | Movimento libero | free | righe libere inserite dall'utente (≥2, quadrate) | — | opzionale |
| **GIR** | Giroconto | free | come LIB, senza anagrafica | — | — |
| **SAL** | Stipendi/salari | free (template) | D costo personale (3.3.01) · A dipendenti c/retrib. (2.4.06) · A Erario/INPS (2.4.05/2.4.04) | — | scadenze F24/16 |

Comportamento comune: la causale precompila i conti dai ruoli (`party_subaccount` → partitario del soggetto scelto; `vat` → 1.4.02/2.4.02 secondo il registro; `cash_bank` → scelta tra 1.1.01/1.1.02); l'utente può sostituire i conti proposti purché le invarianti reggano.

---

## 10. Piano dei conti standard italiano (seed, livelli 1–4)

Struttura a 4 livelli: `L1` sezione, `L2` mastro, `L3` conto (postabile), `L4` sottoconto/partitario (postabile). Codifica `N.N.NN[.NNN]`. Estratto delle categorie principali (il seed completo è in `parties/seeds/account_plan_standard.py`).

```
1        ATTIVO                                          [asset, D]
1.1      Disponibilità liquide
1.1.01     Cassa contanti
1.1.02     Banca c/c                       → 1.1.02.001 Banca Intesa c/c, … (L4 per conto corrente)
1.1.03     Carte prepagate / PayPal
1.2      Crediti commerciali
1.2.01     Crediti verso clienti (mastro)  → 1.2.01.001… partitari cliente (L4 auto-generati)
1.2.02     Fatture da emettere
1.2.03     Fondo svalutazione crediti (−)
1.2.04     Effetti attivi / Ri.Ba. attive
1.3      Altri crediti
1.3.01     Crediti verso dipendenti
1.3.02     Anticipi a fornitori
1.3.03     Crediti diversi
1.4      Crediti erariali
1.4.01     Erario c/acconti IRES-IRPEF-IRAP
1.4.02     IVA ns/credito (IVA acquisti)
1.4.03     Credito IVA da liquidazione
1.4.04     Erario c/ritenute subite
1.5      Immobilizzazioni immateriali
1.5.01     Software e licenze
1.5.02     Avviamento
1.5.09     Fondi ammortamento imm. immateriali (−)
1.6      Immobilizzazioni materiali
1.6.01     Fabbricati
1.6.02     Impianti e macchinari
1.6.03     Attrezzature
1.6.04     Macchine d'ufficio e hardware
1.6.05     Automezzi
1.6.09     Fondi ammortamento imm. materiali (−)
1.7      Immobilizzazioni finanziarie
1.7.01     Partecipazioni
1.7.02     Depositi cauzionali
1.8      Rimanenze
1.8.01     Rimanenze merci
1.8.02     Rimanenze materie prime
1.9      Ratei e risconti attivi
1.9.01     Ratei attivi
1.9.02     Risconti attivi

2        PASSIVO E PATRIMONIO NETTO                      [liability/equity, A]
2.1      Patrimonio netto
2.1.01     Capitale sociale
2.1.02     Riserva legale
2.1.03     Altre riserve
2.1.04     Utili (perdite) portati a nuovo
2.1.05     Utile (perdita) d'esercizio
2.2      Debiti commerciali
2.2.01     Debiti verso fornitori (mastro) → 2.2.01.001… partitari fornitore (L4 auto-generati)
2.2.02     Fatture da ricevere
2.2.03     Effetti passivi
2.2.04     Anticipi da clienti
2.3      Debiti finanziari
2.3.01     Banche c/anticipi
2.3.02     Mutui passivi
2.3.03     Finanziamenti soci
2.4      Debiti erariali, previdenziali e verso il personale
2.4.01     Erario c/IRES-IRPEF-IRAP
2.4.02     IVA ns/debito (IVA vendite)
2.4.03     Erario c/IVA da liquidazione
2.4.04     INPS c/contributi
2.4.05     Erario c/ritenute da versare
2.4.06     Dipendenti c/retribuzioni
2.4.07     Debiti per TFR
2.5      Fondi rischi e oneri
2.5.01     Fondo imposte
2.5.02     Altri fondi
2.6      Ratei e risconti passivi
2.6.01     Ratei passivi
2.6.02     Risconti passivi

3        COSTI                                           [expense, D]
3.1      Acquisti
3.1.01     Merci c/acquisti
3.1.02     Materie prime c/acquisti
3.1.03     Materiale di consumo
3.2      Servizi
3.2.01     Lavorazioni di terzi
3.2.02     Utenze (energia, acqua, gas)
3.2.03     Telefonia e connettività
3.2.04     Manutenzioni e riparazioni
3.2.05     Consulenze e prestazioni professionali
3.2.06     Pubblicità e marketing
3.2.07     Assicurazioni
3.2.08     Trasporti e spedizioni
3.2.09     Spese bancarie e commissioni
3.2.10     Viaggi e trasferte
3.3      Costo del personale
3.3.01     Salari e stipendi
3.3.02     Oneri sociali
3.3.03     TFR accantonamento
3.4      Godimento beni di terzi
3.4.01     Affitti passivi
3.4.02     Noleggi e leasing
3.5      Ammortamenti e svalutazioni
3.5.01     Ammortamento imm. immateriali
3.5.02     Ammortamento imm. materiali
3.5.03     Svalutazione crediti
3.6      Oneri diversi di gestione
3.6.01     Imposte e tasse deducibili (bolli, vidimazioni)
3.6.02     Sanzioni e oneri indeducibili
3.6.03     Sopravvenienze passive
3.7      Oneri finanziari
3.7.01     Interessi passivi bancari
3.7.02     Interessi passivi su mutui
3.8      Variazioni rimanenze (costi)
3.8.01     Rimanenze iniziali
3.9      Imposte d'esercizio
3.9.01     IRES corrente
3.9.02     IRAP corrente

4        RICAVI                                          [revenue, A]
4.1      Ricavi delle vendite e prestazioni
4.1.01     Ricavi vendite merci/prodotti
4.1.02     Ricavi prestazioni di servizi
4.1.03     Resi e abbuoni su vendite (−)
4.2      Altri ricavi e proventi
4.2.01     Affitti attivi
4.2.02     Sopravvenienze attive
4.2.03     Contributi in conto esercizio
4.3      Proventi finanziari
4.3.01     Interessi attivi bancari
4.4      Variazioni rimanenze (ricavi)
4.4.01     Rimanenze finali

5        CONTI DI CHIUSURA E TRANSITORI                  [memorandum]
5.1      Risultato e chiusura
5.1.01     Conto economico di chiusura
5.1.02     Stato patrimoniale di chiusura / bilancio apertura
5.2      Conti transitori
5.2.01     Transitorio incassi POS
5.2.02     Partite da sistemare
```

Note: i conti segnati (−) sono rettificativi (normal_side opposto alla sezione). I mastri 1.2.01 e 2.2.01 hanno `is_subaccount_parent=true`: creando una `Party` il sistema genera il partitario L4 col progressivo successivo. La numerazione L4 dei partitari è per-azienda.

---

## Revisioni necessarie

Domande aperte per il titolare del progetto:

1. **Profondità del piano dei conti**: 4 livelli bastano per tutte le aziende clienti o serve un livello 5 per commesse/centri di costo? In alternativa: dimensione analitica separata (tag centro di costo su `journal_line`)?
2. **Codifica conti**: confermare il formato `N.N.NN.NNN` o preferite la codifica numerica compatta usata dal gestionale attuale dello studio (per facilitare migrazione dati)?
3. **Partite aperte**: lo scadenzario a rate qui modellato basta, o serve una vera gestione partite (matching many-to-many incassi↔fatture con abbuoni e differenze cambio)? Impatta `ScheduledPayment.settlement_entry_id` (oggi solo l'ultima scrittura).
4. **IVA per cassa (art. 32-bis)** e **split payment**: quante aziende clienti li usano? Il flag `is_deferred` è predisposto ma la liquidazione differita richiede logica dedicata (esigibilità all'incasso).
5. **Corrispettivi**: le aziende retail con registratore telematico rientrano nel perimetro? Il registro `corrispettivi` è previsto ma senza import da RT.
6. **Ritenute**: aliquota base 20% su imponibile 100% è il caso comune; servono le casistiche agenti (23% sul 50%) e condominio (4%)? Meglio tabella `withholding_kind` di lookup?
7. **Bilancio CEE**: serve la riclassificazione civilistica (art. 2424/2425 c.c.) già dal domain model (campo `cee_code` su `account`) o si rimanda alla Fase 4?
8. **Numerazione partitari**: i sottoconti cliente/fornitore devono riprendere i codici del vecchio gestionale in fase di migrazione?
9. **Cespiti**: confermare che il registro cespiti (Fase 4) introdurrà entità dedicate (`Asset`, `DepreciationPlan`) — qui volutamente escluse.
