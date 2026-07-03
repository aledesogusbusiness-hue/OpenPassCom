export interface User { id: string; email: string; nome: string; cognome: string; role: string }
export interface ClientEntity { id: string; studio_id: string; ragione_sociale: string; codice_fiscale: string; partita_iva: string; regime_fiscale: 'ordinario' | 'semplificato' | 'forfettario'; email?: string; pec?: string; telefono?: string; indirizzo?: string; cap?: string; citta?: string; provincia?: string; is_active: boolean; created_at: string }
export interface FiscalYear { id: string; client_entity_id: string; anno: number; data_inizio: string; data_fine: string; stato: string }
export interface AccountPlan { id: string; nome: string; is_default: boolean; created_at: string }
export interface Account { id: string; codice: string; nome: string; account_type_id: string; parent_id?: string; livello: number; is_active: boolean }
export interface AccountType { id: string; tipo_codice: string; nome: string; posizione_bilancio: string }
export interface JournalLine { id: string; journal_entry_id: string; account_id: string; dare: string; avere: string; descrizione?: string }
export interface JournalEntry { id: string; numero_registrazione: number; data_registrazione: string; descrizione: string; causale: string; stato: 'draft' | 'posted' | 'reversed'; lines?: JournalLine[]; created_at: string }
export interface VatEntry { id: string; data_documento: string; numero_documento?: string; controparte?: string; imponibile: string; aliquota: number; imposta: string; created_at: string }
export interface VatSettlement { id: string; periodo: string; tipo_periodo: string; iva_vendite: string; iva_acquisti: string; credito_precedente: string; debito_versare: string; credito_periodo: string; stato: string; data_versamento?: string; f24_riferimento?: string }
export interface WithholdingTax { id: string; tipo: string; codice_tributo: string; imponibile: string; aliquota_pct: string; importo_ritenuta: string; mese_competenza: number; anno_competenza: number; stato: string; data_versamento?: string; f24_riferimento?: string }
export interface FatturaPAImport { id: string; filename: string; stato: string; errore_msg?: string; created_at: string }
export interface FixedAsset { id: string; codice: string; descrizione: string; categoria: string; costo_storico: string; data_acquisto: string; aliquota_ammortamento: string; metodo: string; is_active: boolean }
export interface DepreciationEntry { id: string; anno: number; valore_iniziale: string; quota_ammortamento: string; fondo_ammortamento: string; valore_netto_finale: string; stato: string }
export interface YearClosing { id: string; fiscal_year_id: string; stato: string; data_chiusura?: string; totale_attivo?: string; totale_passivo?: string; totale_ricavi?: string; totale_costi?: string; utile_perdita?: string }
export interface DashboardSummary { totale_clienti: number; clienti_attivi: number; esercizi_aperti: number; registrazioni_bozza: number; registrazioni_postate: number; scadenze_aperte: number; task_aperti: number; task_urgenti: number }
export interface StudioTask { id: string; titolo: string; tipo: string; priorita: string; stato: string; data_scadenza?: string; client_entity_id?: string; fiscal_year_id?: string; descrizione?: string; assegnato_a?: string; created_at: string }
export interface BankStatement { id: string; client_entity_id: string; iban: string; data_inizio: string; data_fine: string; saldo_iniziale: string; saldo_finale: string; filename?: string; created_at: string }
export interface BankTransaction { id: string; bank_statement_id: string; data_valuta: string; data_contabile: string; descrizione: string; importo: string; tipo: 'entrata' | 'uscita'; stato_riconciliazione: 'da_riconciliare' | 'riconciliata' | 'irrilevante'; journal_entry_id?: string }
export interface ConservatoreLog { id: string; tipo_documento: string; stato: string; data_invio?: string; riferimento_esterno?: string; periodo?: string; note?: string; created_at: string }
export interface BilancioVerifica { righe: Array<{ codice: string; nome: string; dare_totale: string; avere_totale: string }>; totale_dare: string; totale_avere: string }
export interface StatoPatrimoniale { attivo: Array<{ conto: string; importo: string }>; passivo: Array<{ conto: string; importo: string }>; totale_attivo: string; totale_passivo: string }
export interface ContoEconomico { ricavi: Array<{ conto: string; importo: string }>; costi: Array<{ conto: string; importo: string }>; totale_ricavi: string; totale_costi: string; utile_perdita: string }
export interface F24Prospetto { periodo: string; iva_dovuta: string; data_scadenza: string }
export interface ApiError { detail: string | Array<{ msg: string; loc: string[] }> }
