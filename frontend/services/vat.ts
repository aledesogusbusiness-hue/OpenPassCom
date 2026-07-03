import { apiClient } from '@/lib/api-client'
import type { VatEntry, VatSettlement, WithholdingTax, FatturaPAImport, F24Ritenuta } from '@/types'

export interface CreateVatEntryInput {
  tipo: 'vendite' | 'acquisti'
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

export interface ElaborateFatturaPAInput {
  account_id_fornitore: string
  account_id_iva: string
  account_id_debito: string
}

export const vatService = {
  async listEntries(clientId: string, fiscalYearId: string): Promise<Array<VatEntry & { tipo: 'vendite' | 'acquisti' }>> {
    const [vendite, acquisti] = await Promise.all([
      apiClient.get<VatEntry[]>(
        `/api/v1/clients/${clientId}/fiscal-years/${fiscalYearId}/vat/vendite`
      ),
      apiClient.get<VatEntry[]>(
        `/api/v1/clients/${clientId}/fiscal-years/${fiscalYearId}/vat/acquisti`
      ),
    ])
    return [
      ...vendite.map((e) => ({ ...e, tipo: 'vendite' as const })),
      ...acquisti.map((e) => ({ ...e, tipo: 'acquisti' as const })),
    ]
  },

  createEntry(clientId: string, fiscalYearId: string, data: CreateVatEntryInput): Promise<VatEntry> {
    return apiClient.post<VatEntry>(
      `/api/v1/clients/${clientId}/fiscal-years/${fiscalYearId}/vat/entries`,
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
    data: { periodo: string; credito_precedente?: string }
  ): Promise<VatSettlement> {
    return apiClient.post<VatSettlement>(
      `/api/v1/clients/${clientId}/fiscal-years/${fiscalYearId}/vat-settlements/compute`,
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
      `/api/v1/clients/${clientId}/fiscal-years/${fiscalYearId}/vat-settlements/${settlementId}/mark-versata`,
      data
    )
  },

  listWithholding(clientId: string, fiscalYearId: string): Promise<WithholdingTax[]> {
    return apiClient.get<WithholdingTax[]>(
      `/api/v1/clients/${clientId}/fiscal-years/${fiscalYearId}/withholdings`
    )
  },

  createWithholding(
    clientId: string,
    fiscalYearId: string,
    data: CreateWithholdingInput
  ): Promise<WithholdingTax> {
    return apiClient.post<WithholdingTax>(
      `/api/v1/clients/${clientId}/fiscal-years/${fiscalYearId}/withholdings`,
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
      `/api/v1/clients/${clientId}/fiscal-years/${fiscalYearId}/withholdings/${withholdingId}/mark-versata`,
      data
    )
  },

  getWithholdingF24(
    clientId: string,
    fiscalYearId: string,
    mese: number,
    anno: number
  ): Promise<F24Ritenuta> {
    return apiClient.get<F24Ritenuta>(
      `/api/v1/clients/${clientId}/fiscal-years/${fiscalYearId}/withholdings/f24?mese=${mese}&anno=${anno}`
    )
  },

  listFatturePa(clientId: string, fiscalYearId: string): Promise<FatturaPAImport[]> {
    return apiClient.get<FatturaPAImport[]>(
      `/api/v1/clients/${clientId}/fiscal-years/${fiscalYearId}/fatture-pa`
    )
  },

  async uploadFatturaPA(clientId: string, fiscalYearId: string, file: File): Promise<FatturaPAImport> {
    const xmlContent = await file.text()
    return apiClient.post<FatturaPAImport>(
      `/api/v1/clients/${clientId}/fiscal-years/${fiscalYearId}/fatture-pa/import`,
      { filename: file.name, xml_content: xmlContent }
    )
  },

  elaborateFatturaPA(
    clientId: string,
    fiscalYearId: string,
    importId: string,
    data: ElaborateFatturaPAInput
  ): Promise<FatturaPAImport> {
    return apiClient.post<FatturaPAImport>(
      `/api/v1/clients/${clientId}/fiscal-years/${fiscalYearId}/fatture-pa/${importId}/elaborate`,
      data
    )
  },
}
