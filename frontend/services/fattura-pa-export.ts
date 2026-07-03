import { apiClient } from '@/lib/api-client'

export interface FatturaPAExportLineInput {
  descrizione: string
  quantita: string
  unita_misura?: string
  prezzo_unitario: string
  aliquota_iva: number
}

export interface FatturaPAExportLine {
  id: string
  numero_linea: number
  descrizione: string
  quantita: string
  unita_misura?: string
  prezzo_unitario: string
  aliquota_iva: string
}

export interface CreateFatturaPAExportInput {
  journal_entry_id?: string
  tipo_documento: string
  numero_fattura: string
  data_fattura: string
  cedente_indirizzo: string
  cedente_cap: string
  cedente_comune: string
  cedente_provincia: string
  destinatario_denominazione: string
  destinatario_partita_iva?: string
  destinatario_codice_fiscale?: string
  destinatario_indirizzo: string
  destinatario_cap: string
  destinatario_comune: string
  destinatario_provincia: string
  destinatario_codice_sdi: string
  destinatario_pec?: string
  righe: FatturaPAExportLineInput[]
}

export interface FatturaPAExport {
  id: string
  studio_id: string
  client_entity_id: string
  fiscal_year_id: string
  journal_entry_id?: string
  tipo_documento: string
  numero_fattura: string
  data_fattura: string
  destinatario_denominazione: string
  destinatario_partita_iva?: string
  destinatario_codice_fiscale?: string
  destinatario_codice_sdi: string
  destinatario_pec?: string
  stato: 'bozza' | 'generata' | 'inviata' | 'accettata' | 'scartata' | 'consegnata' | 'errore'
  progressivo_invio?: string
  identificativo_sdi?: string
  data_invio?: string
  data_esito?: string
  esito_messaggio?: string
  errore_msg?: string
  created_at: string
  righe: FatturaPAExportLine[]
}

export const fatturaPaExportService = {
  list(clientId: string, fiscalYearId: string): Promise<FatturaPAExport[]> {
    return apiClient.get<FatturaPAExport[]>(
      `/api/v1/clients/${clientId}/fiscal-years/${fiscalYearId}/fatture-pa-export`
    )
  },

  create(
    clientId: string,
    fiscalYearId: string,
    data: CreateFatturaPAExportInput
  ): Promise<FatturaPAExport> {
    return apiClient.post<FatturaPAExport>(
      `/api/v1/clients/${clientId}/fiscal-years/${fiscalYearId}/fatture-pa-export`,
      data
    )
  },

  generateXml(clientId: string, fiscalYearId: string, exportId: string): Promise<FatturaPAExport> {
    return apiClient.post<FatturaPAExport>(
      `/api/v1/clients/${clientId}/fiscal-years/${fiscalYearId}/fatture-pa-export/${exportId}/generate-xml`,
      {}
    )
  },

  download(
    clientId: string,
    fiscalYearId: string,
    exportId: string
  ): Promise<{ blob: Blob; filename: string }> {
    return apiClient.getBlob(
      `/api/v1/clients/${clientId}/fiscal-years/${fiscalYearId}/fatture-pa-export/${exportId}/download`
    )
  },

  markInviata(
    clientId: string,
    fiscalYearId: string,
    exportId: string,
    identificativoSdi?: string
  ): Promise<FatturaPAExport> {
    return apiClient.post<FatturaPAExport>(
      `/api/v1/clients/${clientId}/fiscal-years/${fiscalYearId}/fatture-pa-export/${exportId}/mark-inviata`,
      { identificativo_sdi: identificativoSdi }
    )
  },

  markEsito(
    clientId: string,
    fiscalYearId: string,
    exportId: string,
    esito: 'accettata' | 'scartata' | 'consegnata',
    messaggio?: string
  ): Promise<FatturaPAExport> {
    return apiClient.post<FatturaPAExport>(
      `/api/v1/clients/${clientId}/fiscal-years/${fiscalYearId}/fatture-pa-export/${exportId}/mark-esito`,
      { esito, messaggio }
    )
  },
}
