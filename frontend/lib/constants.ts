export const REGIME_FISCALE_OPTIONS = [
  { value: 'ordinario', label: 'Ordinario' },
  { value: 'semplificato', label: 'Semplificato' },
  { value: 'forfettario', label: 'Forfettario' },
] as const

export const CAUSALE_OPTIONS = [
  { value: 'FV', label: 'FV — Fattura Vendita' },
  { value: 'FA', label: 'FA — Fattura Acquisto' },
  { value: 'IN', label: 'IN — Incasso' },
  { value: 'PG', label: 'PG — Pagamento' },
  { value: 'PN', label: 'PN — Prima Nota Generica' },
] as const

export const TASK_TIPO_OPTIONS = [
  { value: 'scadenza_iva', label: 'Scadenza IVA' },
  { value: 'versamento_ritenute', label: 'Versamento Ritenute' },
  { value: 'chiusura_bilancio', label: 'Chiusura Bilancio' },
  { value: 'generico', label: 'Generico' },
] as const

export const TASK_PRIORITA_OPTIONS = [
  { value: 'bassa', label: 'Bassa' },
  { value: 'normale', label: 'Normale' },
  { value: 'alta', label: 'Alta' },
  { value: 'urgente', label: 'Urgente' },
] as const

export const CONSERVATORE_TIPO_OPTIONS = [
  { value: 'libro_giornale', label: 'Libro Giornale' },
  { value: 'registro_iva', label: 'Registro IVA' },
  { value: 'bilancio', label: 'Bilancio' },
] as const
