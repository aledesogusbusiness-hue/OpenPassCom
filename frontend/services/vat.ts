import { apiClient } from '@/lib/api-client'
import type { VatEntry, VatSettlement, WithholdingTax, FatturaPAImport, F24Prospetto } from '@/types'

export interface CreateVatEntryInput {
  vat_register_id: string
  journal_entry_id: string
  data_documento: string
  numero_documento?: string
  controparte?: string
  imponibile: string
  aliquota: number
  imposta: string
}

export interface CreateWithholdingInput {
  tipo: string
  imponibile: string
  aliquota_pct: string
  mese_competenza: number
  anno_competenza: number
  journal_entry_id?: string
}

export const vatService = {
  listEntries(clientId: string, fiscalYearId: string): Promise<VatEntry[]> {
    return apiClient.get<VatEntry[]>(
      `/api/v1/clients/${clientId}/fiscal-years/${fiscalYearId}/vat-entries`
    )
  },

  createEntry(clientId: string, fiscalYearId: string, data: CreateVatEntryInput): Promise<VatEntry> {
    return apiClient.post<VatEntry>(
      `/api/v1/clients/${clientId}/fiscal-years/${fiscalYearId}/vat-entries`,
      data
    )
  },

  listSettlements(clientId: string, fiscalYearId: string): Promise<VatSettlement[]> {
    return apiClient.get<VatSettlement[]>(
      `/api/v1/clients/${clientId}/fiscal-years/${fiscalYearId}/vat-settlements`
    )
  },

  createSettlement(
    clientId: string,
    fiscalYearId: string,
    data: { periodo: string; tipo_periodo: string }
  ): Promise<VatSettlement> {
    return apiClient.post<VatSettlement>(
      `/api/v1/clients/${clientId}/fiscal-years/${fiscalYearId}/vat-settlements`,
      data
    )
  },

  markSettlementVersata(
    clientId: string,
    fiscalYearId: string,
    settlementId: string,
    data: { data_versamento: string; f24_riferimento?: string }
  ): Promise<VatSettlement> {
    return apiClient.post<VatSettlement>(
      `/api/v1/clients/${clientId}/fiscal-years/${fiscalYearId}/vat-settlements/${settlementId}/versata`,
      data
    )
  },

  getF24(clientId: string, fiscalYearId: string, periodo: string): Promise<F24Prospetto> {
    return apiClient.get<F24Prospetto>(
      `/api/v1/clients/${clientId}/fiscal-years/${fiscalYearId}/f24/${periodo}`
    )
  },

  listWithholding(clientId: string, fiscalYearId: string): Promise<WithholdingTax[]> {
    return apiClient.get<WithholdingTax[]>(
      `/api/v1/clients/${clientId}/fiscal-years/${fiscalYearId}/withholding-taxes`
    )
  },

  createWithholding(
    clientId: string,
    fiscalYearId: string,
    data: CreateWithholdingInput
  ): Promise<WithholdingTax> {
    return apiClient.post<WithholdingTax>(
      `/api/v1/clients/${clientId}/fiscal-years/${fiscalYearId}/withholding-taxes`,
      data
    )
  },

  markWithholdingVersata(
    clientId: string,
    fiscalYearId: string,
    withholdingId: string,
    data: { data_versamento: string; f24_riferimento?: string }
  ): Promise<WithholdingTax> {
    return apiClient.post<WithholdingTax>(
      `/api/v1/clients/${clientId}/fiscal-years/${fiscalYearId}/withholding-taxes/${withholdingId}/versata`,
      data
    )
  },

  listFatturePa(clientId: string, fiscalYearId: string): Promise<FatturaPAImport[]> {
    return apiClient.get<FatturaPAImport[]>(
      `/api/v1/clients/${clientId}/fiscal-years/${fiscalYearId}/fatture-pa`
    )
  },

  uploadFatturaPA(clientId: string, fiscalYearId: string, file: File): Promise<FatturaPAImport> {
    const formData = new FormData()
    formData.append('file', file)
    return apiClient.postForm<FatturaPAImport>(
      `/api/v1/clients/${clientId}/fiscal-years/${fiscalYearId}/fatture-pa/upload`,
      formData
    )
  },

  elaborateFatturaPA(
    clientId: string,
    fiscalYearId: string,
    importId: string
  ): Promise<FatturaPAImport> {
    return apiClient.post<FatturaPAImport>(
      `/api/v1/clients/${clientId}/fiscal-years/${fiscalYearId}/fatture-pa/${importId}/elaborate`
    )
  },
}
