import { apiClient } from '@/lib/api-client'
import type { StatoPatrimoniale, ContoEconomico, YearClosing, FixedAsset, DepreciationEntry } from '@/types'

export interface CreateFixedAssetInput {
  codice: string
  descrizione: string
  categoria: string
  costo_storico: string
  data_acquisto: string
  aliquota_ammortamento: string
  metodo?: 'quote_costanti' | 'decrescente'
  account_id?: string
  note?: string
}

export const balanceService = {
  getStatoPatrimoniale(clientId: string, fiscalYearId: string): Promise<StatoPatrimoniale> {
    return apiClient.get<StatoPatrimoniale>(
      `/api/v1/clients/${clientId}/fiscal-years/${fiscalYearId}/stato-patrimoniale`
    )
  },

  getContoEconomico(clientId: string, fiscalYearId: string): Promise<ContoEconomico> {
    return apiClient.get<ContoEconomico>(
      `/api/v1/clients/${clientId}/fiscal-years/${fiscalYearId}/conto-economico`
    )
  },

  closeYear(clientId: string, fiscalYearId: string): Promise<YearClosing> {
    return apiClient.post<YearClosing>(
      `/api/v1/clients/${clientId}/fiscal-years/${fiscalYearId}/close`,
      {}
    )
  },

  listFixedAssets(clientId: string): Promise<FixedAsset[]> {
    return apiClient.get<FixedAsset[]>(`/api/v1/clients/${clientId}/fixed-assets`)
  },

  createFixedAsset(clientId: string, data: CreateFixedAssetInput): Promise<FixedAsset> {
    return apiClient.post<FixedAsset>(`/api/v1/clients/${clientId}/fixed-assets`, data)
  },

  computePlan(clientId: string, assetId: string): Promise<DepreciationEntry[]> {
    return apiClient.post<DepreciationEntry[]>(
      `/api/v1/clients/${clientId}/fixed-assets/${assetId}/compute-plan`,
      {}
    )
  },

  getPlan(clientId: string, assetId: string): Promise<DepreciationEntry[]> {
    return apiClient.get<DepreciationEntry[]>(
      `/api/v1/clients/${clientId}/fixed-assets/${assetId}/plan`
    )
  },

  exportBilancio(
    clientId: string,
    fiscalYearId: string,
    format: 'pdf' | 'xlsx'
  ): Promise<{ blob: Blob; filename: string }> {
    return apiClient.getBlob(
      `/api/v1/clients/${clientId}/fiscal-years/${fiscalYearId}/export/bilancio?format=${format}`
    )
  },
}
