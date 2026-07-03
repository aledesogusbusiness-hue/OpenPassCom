'use client'

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { balanceService } from '@/services/balance'
import type { CreateFixedAssetInput } from '@/services/balance'
import { triggerDownload } from '@/lib/utils'

export function useStatoPatrimoniale(clientId: string, fiscalYearId: string) {
  return useQuery({
    queryKey: ['stato-patrimoniale', clientId, fiscalYearId],
    queryFn: () => balanceService.getStatoPatrimoniale(clientId, fiscalYearId),
    enabled: !!clientId && !!fiscalYearId,
  })
}

export function useContoEconomico(clientId: string, fiscalYearId: string) {
  return useQuery({
    queryKey: ['conto-economico', clientId, fiscalYearId],
    queryFn: () => balanceService.getContoEconomico(clientId, fiscalYearId),
    enabled: !!clientId && !!fiscalYearId,
  })
}

export function useFixedAssets(clientId: string) {
  return useQuery({
    queryKey: ['fixed-assets', clientId],
    queryFn: () => balanceService.listFixedAssets(clientId),
    enabled: !!clientId,
  })
}

export function useCreateFixedAsset(clientId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: CreateFixedAssetInput) =>
      balanceService.createFixedAsset(clientId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['fixed-assets', clientId] })
    },
  })
}

export function useComputePlan(clientId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (assetId: string) => balanceService.computePlan(clientId, assetId),
    onSuccess: (_data, assetId) => {
      queryClient.invalidateQueries({ queryKey: ['fixed-assets', clientId] })
      queryClient.invalidateQueries({ queryKey: ['depreciation-plan', clientId, assetId] })
    },
  })
}

export function useDepreciationPlan(clientId: string, assetId: string) {
  return useQuery({
    queryKey: ['depreciation-plan', clientId, assetId],
    queryFn: () => balanceService.getPlan(clientId, assetId),
    enabled: !!clientId && !!assetId,
  })
}

export function useExportBilancio(clientId: string, fiscalYearId: string) {
  return useMutation({
    mutationFn: async (format: 'pdf' | 'xlsx') => {
      const { blob, filename } = await balanceService.exportBilancio(clientId, fiscalYearId, format)
      triggerDownload(blob, filename)
    },
  })
}

export function useCloseYear(clientId: string, fiscalYearId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => balanceService.closeYear(clientId, fiscalYearId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['fiscal-years', clientId] })
      queryClient.invalidateQueries({
        queryKey: ['stato-patrimoniale', clientId, fiscalYearId],
      })
      queryClient.invalidateQueries({
        queryKey: ['conto-economico', clientId, fiscalYearId],
      })
    },
  })
}
