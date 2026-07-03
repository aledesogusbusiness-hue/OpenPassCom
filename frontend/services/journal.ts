import { apiClient } from '@/lib/api-client'
import type { JournalEntry, BilancioVoce } from '@/types'

export interface CreateJournalLineInput {
  account_id: string
  dare: string
  avere: string
  descrizione?: string
}

export interface CreateJournalEntryInput {
  data_registrazione: string
  descrizione: string
  causale: string
  lines: CreateJournalLineInput[]
}

export const journalService = {
  list(clientId: string, fiscalYearId: string): Promise<JournalEntry[]> {
    return apiClient.get<JournalEntry[]>(
      `/api/v1/clients/${clientId}/fiscal-years/${fiscalYearId}/journal-entries`
    )
  },

  get(clientId: string, fiscalYearId: string, entryId: string): Promise<JournalEntry> {
    return apiClient.get<JournalEntry>(
      `/api/v1/clients/${clientId}/fiscal-years/${fiscalYearId}/journal-entries/${entryId}`
    )
  },

  create(clientId: string, fiscalYearId: string, data: CreateJournalEntryInput): Promise<JournalEntry> {
    return apiClient.post<JournalEntry>(
      `/api/v1/clients/${clientId}/fiscal-years/${fiscalYearId}/journal-entries`,
      data
    )
  },

  post(clientId: string, fiscalYearId: string, entryId: string): Promise<JournalEntry> {
    return apiClient.post<JournalEntry>(
      `/api/v1/clients/${clientId}/fiscal-years/${fiscalYearId}/journal-entries/${entryId}/post`
    )
  },

  reverse(clientId: string, fiscalYearId: string, entryId: string): Promise<JournalEntry> {
    return apiClient.post<JournalEntry>(
      `/api/v1/clients/${clientId}/fiscal-years/${fiscalYearId}/journal-entries/${entryId}/reverse`
    )
  },

  getBilancioVerifica(clientId: string, fiscalYearId: string): Promise<BilancioVoce[]> {
    return apiClient.get<BilancioVoce[]>(
      `/api/v1/clients/${clientId}/fiscal-years/${fiscalYearId}/bilancio-verifica`
    )
  },

  exportLibroGiornale(
    clientId: string,
    fiscalYearId: string,
    format: 'pdf' | 'xlsx'
  ): Promise<{ blob: Blob; filename: string }> {
    return apiClient.getBlob(
      `/api/v1/clients/${clientId}/fiscal-years/${fiscalYearId}/export/libro-giornale?format=${format}`
    )
  },
}
