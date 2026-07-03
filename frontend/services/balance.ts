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
      `/api/v1/clients/${clientId}/fiscal-years/${fiscalYearId}/balance/stato-patrimoniale`
    )
  },

  getContoEconomico(clientId: string, fiscalYearId: string): Promise<ContoEconomico> {
    return apiClient.get<ContoEconomico>(
      `/api/v1/clients/${clientId}/fiscal-years/${fiscalYearId}/balance/conto-economico`
    )
  },

  closeYear(clientId: string, fiscalYearId: string): Promise<YearClosing> {
    return apiClient.post<YearClosing>(
      `/api/v1/clients/${clientId}/fiscal-years/${fiscalYearId}/close`
    )
  },

  listFixedAssets(clientId: string, fiscalYearId: string): Promise<FixedAsset[]> {
    return apiClient.get<FixedAsset[]>(
      `/api/v1/clients/${clientId}/fiscal-years/${fiscalYearId}/fixed-assets`
    )
  },

  createFixedAsset(
    clientId: string,
    fiscalYearId: string,
    data: CreateFixedAssetInput
  ): Promise<FixedAsset> {
    return apiClient.post<FixedAsset>(
      `/api/v1/clients/${clientId}/fiscal-years/${fiscalYearId}/fixed-assets`,
      data
    )
  },

  depreciate(clientId: string, fiscalYearId: string, assetId: string): Promise<DepreciationEntry> {
    return apiClient.post<DepreciationEntry>(
      `/api/v1/clients/${clientId}/fiscal-years/${fiscalYearId}/fixed-assets/${assetId}/depreciate`
    )
  },

  getDepreciationSchedule(
    clientId: string,
    fiscalYearId: string,
    assetId: string
  ): Promise<DepreciationEntry[]> {
    return apiClient.get<DepreciationEntry[]>(
      `/api/v1/clients/${clientId}/fiscal-years/${fiscalYearId}/fixed-assets/${assetId}/depreciation-schedule`
    )
  },
}
