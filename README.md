# OpenPassCom

Piattaforma contabile API-first per studi commercialistici italiani, ispirata a Passepartout/Passcom.

## Stack Tecnologico

| Componente | Tecnologia |
|---|---|
| Runtime | Python 3.12 |
| Framework | FastAPI (async) |
| Database | PostgreSQL 16 — `NUMERIC(15,2)` per tutti gli importi |
| ORM | SQLAlchemy 2.0 async + asyncpg |
| Migrazioni | Alembic |
| Schemi | Pydantic v2 |
| Auth | JWT HS256 — python-jose + passlib/bcrypt |
| Test | pytest-asyncio + httpx + SQLite in-memory |

## Struttura del Progetto

```
registro-contabilita/
├── backend/
│   ├── alembic/
│   │   └── versions/
│   │       ├── 0001_initial_schema.py
│   │       ├── 0002_journal_vat.py
│   │       ├── 0003_tax_settlement.py
│   │       ├── 0004_balance_assets.py
│   │       └── 0005_phase56_studio_bank.py
│   ├── app/
│   │   ├── config.py           # Settings Pydantic — STUDIO_ID, SECRET_KEY, DATABASE_URL
│   │   ├── database.py         # Engine async + get_db dependency
│   │   ├── dependencies.py     # get_current_user (JWT decode)
│   │   ├── main.py             # FastAPI app, middleware, include_router
│   │   ├── middleware.py       # StudioTenantMiddleware
│   │   ├── models/
│   │   │   ├── base.py         # Base, AuditMixin
│   │   │   ├── auth.py         # User, AuditLog
│   │   │   ├── parties.py      # ClientEntity, FiscalYear
│   │   │   ├── accounting.py   # AccountPlan, AccountType, Account
│   │   │   ├── journal.py      # JournalEntry, JournalLine, SequenceCounter, VatEntry, PaymentSchedule
│   │   │   ├── tax.py          # VatSettlement, WithholdingTax, FatturaPAImport
│   │   │   ├── balance.py      # FixedAsset, DepreciationEntry, YearClosing
│   │   │   └── studio.py       # StudioTask, BankStatement, BankTransaction, ConservatoreLog
│   │   ├── routers/
│   │   │   ├── auth.py
│   │   │   ├── parties.py
│   │   │   ├── accounting.py
│   │   │   ├── journal.py
│   │   │   ├── tax.py
│   │   │   ├── balance_sheet.py
│   │   │   ├── fixed_assets.py
│   │   │   ├── studio.py       # Dashboard + task management
│   │   │   ├── bank.py         # Riconciliazione bancaria
│   │   │   └── conservatore.py # Conservazione digitale
│   │   ├── schemas/
│   │   │   ├── auth.py
│   │   │   ├── parties.py
│   │   │   ├── accounting.py
│   │   │   ├── journal.py
│   │   │   ├── tax.py
│   │   │   ├── balance.py
│   │   │   └── studio.py
│   │   └── services/
│   │       ├── auth_service.py
│   │       ├── parties_service.py
│   │       ├── accounting_service.py
│   │       ├── journal_service.py
│   │       ├── vat_service.py
│   │       ├── fattura_pa_service.py
│   │       ├── balance_sheet_service.py
│   │       ├── fixed_assets_service.py
│   │       ├── studio_task_service.py
│   │       ├── bank_service.py
│   │       └── conservatore_service.py
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_auth.py
│   │   ├── test_parties.py
│   │   ├── test_journal.py
│   │   ├── test_vat.py
│   │   ├── test_vat_settlement.py
│   │   ├── test_withholding.py
│   │   ├── test_fattura_pa.py
│   │   ├── test_fixed_assets.py
│   │   ├── test_balance_sheet.py
│   │   ├── test_studio.py
│   │   ├── test_bank.py
│   │   └── test_conservatore.py
│   ├── .env.example
│   ├── alembic.ini
│   ├── pyproject.toml
│   └── requirements.txt
```

## Quickstart

```bash
cd backend

# 1. Dipendenze
pip install -r requirements.txt

# 2. Variabili d'ambiente
cp .env.example .env
# Modifica DATABASE_URL, SECRET_KEY, STUDIO_ID

# 3. Migrazioni
alembic upgrade head

# 4. Avvio
uvicorn app.main:app --reload

# 5. Test (SQLite in-memory, nessun PostgreSQL richiesto)
python -m pytest tests/ -v
```

## API Endpoints

### Auth
| Metodo | Path | Descrizione |
|--------|------|-------------|
| POST | `/api/v1/auth/login` | Login → JWT |
| GET | `/api/v1/auth/me` | Profilo utente corrente |

### Clienti & Esercizi
| Metodo | Path | Descrizione |
|--------|------|-------------|
| POST | `/api/v1/clients` | Crea cliente |
| GET | `/api/v1/clients` | Lista clienti |
| GET | `/api/v1/clients/{id}` | Dettaglio cliente |
| PATCH | `/api/v1/clients/{id}` | Modifica cliente |
| POST | `/api/v1/clients/{id}/fiscal-years` | Crea esercizio fiscale |
| GET | `/api/v1/clients/{id}/fiscal-years` | Lista esercizi |

### Piano dei Conti
| Metodo | Path | Descrizione |
|--------|------|-------------|
| POST | `/api/v1/clients/{id}/account-plans` | Crea piano dei conti |
| GET | `/api/v1/clients/{id}/account-plans` | Lista piani |
| POST | `/api/v1/clients/{id}/account-plans/{pid}/accounts` | Crea conto |
| GET | `/api/v1/clients/{id}/account-plans/{pid}/accounts` | Lista conti |

### Prima Nota (Libro Giornale)
| Metodo | Path | Descrizione |
|--------|------|-------------|
| POST | `/api/v1/clients/{id}/fiscal-years/{fid}/journal-entries` | Crea registrazione |
| GET | `/api/v1/clients/{id}/fiscal-years/{fid}/journal-entries` | Lista registrazioni |
| GET | `/api/v1/clients/{id}/fiscal-years/{fid}/journal-entries/{eid}` | Dettaglio |
| POST | `/api/v1/clients/{id}/fiscal-years/{fid}/journal-entries/{eid}/post` | Contabilizza (draft→posted) |
| POST | `/api/v1/clients/{id}/fiscal-years/{fid}/journal-entries/{eid}/reverse` | Storna |
| GET | `/api/v1/clients/{id}/fiscal-years/{fid}/bilancio-verifica` | Bilancio di verifica |

### Registro IVA
| Metodo | Path | Descrizione |
|--------|------|-------------|
| POST | `/api/v1/clients/{id}/fiscal-years/{fid}/vat-entries` | Registra movimento IVA |
| GET | `/api/v1/clients/{id}/fiscal-years/{fid}/vat-entries` | Lista movimenti IVA |

### Liquidazione IVA & F24
| Metodo | Path | Descrizione |
|--------|------|-------------|
| POST | `/api/v1/clients/{id}/fiscal-years/{fid}/vat-settlements` | Calcola liquidazione |
| GET | `/api/v1/clients/{id}/fiscal-years/{fid}/vat-settlements` | Lista liquidazioni |
| POST | `/api/v1/clients/{id}/fiscal-years/{fid}/vat-settlements/{sid}/mark-versata` | Marca versata |
| GET | `/api/v1/clients/{id}/fiscal-years/{fid}/f24/{periodo}` | Prospetto F24 IVA |

### Ritenute d'Acconto
| Metodo | Path | Descrizione |
|--------|------|-------------|
| POST | `/api/v1/clients/{id}/fiscal-years/{fid}/withholding-taxes` | Registra ritenuta |
| GET | `/api/v1/clients/{id}/fiscal-years/{fid}/withholding-taxes` | Lista ritenute |
| POST | `/api/v1/clients/{id}/fiscal-years/{fid}/withholding-taxes/{wid}/mark-versata` | Marca versata |
| GET | `/api/v1/clients/{id}/fiscal-years/{fid}/f24-ritenute/{mese}/{anno}` | Prospetto F24 ritenute |

### FatturaPA / SDI
| Metodo | Path | Descrizione |
|--------|------|-------------|
| POST | `/api/v1/clients/{id}/fiscal-years/{fid}/fatture-pa` | Importa XML fattura |
| GET | `/api/v1/clients/{id}/fiscal-years/{fid}/fatture-pa` | Lista importazioni |
| POST | `/api/v1/clients/{id}/fiscal-years/{fid}/fatture-pa/{fid}/elaborate` | Contabilizza fattura |

### Stato Patrimoniale & Conto Economico
| Metodo | Path | Descrizione |
|--------|------|-------------|
| GET | `/api/v1/clients/{id}/fiscal-years/{fid}/stato-patrimoniale` | Stato patrimoniale |
| GET | `/api/v1/clients/{id}/fiscal-years/{fid}/conto-economico` | Conto economico |
| POST | `/api/v1/clients/{id}/fiscal-years/{fid}/close` | Chiudi esercizio |

### Immobilizzazioni & Ammortamenti
| Metodo | Path | Descrizione |
|--------|------|-------------|
| POST | `/api/v1/clients/{id}/fiscal-years/{fid}/fixed-assets` | Crea cespite |
| GET | `/api/v1/clients/{id}/fiscal-years/{fid}/fixed-assets` | Lista cespiti |
| POST | `/api/v1/clients/{id}/fiscal-years/{fid}/fixed-assets/{aid}/depreciate` | Calcola ammortamento |
| GET | `/api/v1/clients/{id}/fiscal-years/{fid}/fixed-assets/{aid}/depreciation-schedule` | Piano ammortamento |

### Dashboard Studio
| Metodo | Path | Descrizione |
|--------|------|-------------|
| GET | `/api/v1/studio/dashboard` | Metriche di studio |
| POST | `/api/v1/studio/tasks` | Crea task |
| GET | `/api/v1/studio/tasks` | Lista task |
| PATCH | `/api/v1/studio/tasks/{tid}` | Aggiorna task |

### Riconciliazione Bancaria
| Metodo | Path | Descrizione |
|--------|------|-------------|
| POST | `/api/v1/clients/{id}/bank-statements` | Importa estratto conto |
| GET | `/api/v1/clients/{id}/bank-statements` | Lista estratti |
| GET | `/api/v1/clients/{id}/bank-statements/{sid}/transactions` | Movimenti bancari |
| POST | `/api/v1/clients/{id}/bank-statements/{sid}/transactions/{tid}/reconcile` | Riconcilia movimento |

### Conservazione Digitale
| Metodo | Path | Descrizione |
|--------|------|-------------|
| POST | `/api/v1/clients/{id}/conservatore` | Invia documento in conservazione |
| GET | `/api/v1/clients/{id}/conservatore` | Lista documenti conservati |

## Modello Dati

### Regimi Fiscali
| Codice | Descrizione | IVA | Ritenute |
|--------|-------------|-----|----------|
| `ordinario` | Regime ordinario | Si | Si |
| `semplificato` | Regime semplificato | Si | Si |
| `forfettario` | Regime forfettario | No (invariante 10bis) | Si |

### Ciclo di Vita Prima Nota
```
draft → posted → reversed
```
- Solo le registrazioni `posted` concorrono al bilancio
- Lo storno crea una nuova registrazione con segni invertiti

### Causali
| Codice | Descrizione |
|--------|-------------|
| `FV` | Fattura vendita |
| `FA` | Fattura acquisto |
| `IN` | Incasso |
| `PG` | Pagamento |
| `PN` | Prima nota generica |

### Tipi Conto (AccountType)
| tipo_codice | posizione_bilancio |
|-------------|-------------------|
| `SP-A` | Stato Patrimoniale Attivo |
| `SP-P` | Stato Patrimoniale Passivo |
| `CE-C` | Conto Economico Costi |
| `CE-R` | Conto Economico Ricavi |

## Invarianti di Dominio

1. **Partita doppia** — `sum(dare) == sum(avere)` obbligatorio su ogni registrazione (422 se non bilanciata)
2. **Invariante 10bis** — clienti in regime forfettario non possono avere VatEntry (422)
3. **Sequenza senza buchi** — `SequenceCounter` usa `SELECT ... FOR UPDATE` su PostgreSQL per garantire `numero_registrazione` progressivo senza buchi
4. **Esercizio chiuso** — non è possibile postare registrazioni su un esercizio con `stato=chiuso`
5. **Storno** — solo registrazioni `posted` possono essere stornate; lo storno imposta `stato=reversed` sull'originale
6. **Ammortamento** — regola del semestre (50% aliquota anno 1); metodi: `quote_costanti` e `decrescente` (double declining balance)
7. **Monostudio** — `STUDIO_ID` fisso da variabile d'ambiente; il middleware inietta l'UUID su ogni richiesta

## Test

```bash
cd backend
python -m pytest tests/ -v
# Nessun PostgreSQL richiesto — usa SQLite in-memory con StaticPool
```

Il seed del database (AccountType + utente admin) viene eseguito una sola volta per processo tramite `asyncio.Lock()` (double-checked locking).

## Variabili d'Ambiente

```env
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/registro_contabilita
SECRET_KEY=cambia-questo-in-produzione
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
STUDIO_ID=00000000-0000-0000-0000-000000000001
```

## Roadmap

- [x] Phase 1 — Auth, clienti, esercizi fiscali, piano dei conti
- [x] Phase 2 — Prima nota, libro giornale, registro IVA, scadenziario
- [x] Phase 3 — Liquidazione IVA, F24, ritenute d'acconto, FatturaPA/SDI
- [x] Phase 4 — Stato patrimoniale, conto economico, cespiti, ammortamenti, chiusura esercizio
- [x] Phase 5 — Dashboard studio, task management
- [x] Phase 6 — Riconciliazione bancaria, conservazione digitale
- [ ] Phase 7 — Export PDF/Excel (bilancio, giornale), firma digitale
- [ ] Phase 8 — Multi-utente, permessi granulari per cliente
- [ ] Phase 9 — Integrazione SDI bidirezionale (invio + ricezione)
- [ ] Phase 10 — Dichiarazioni fiscali (modello 730, IVA annuale)
