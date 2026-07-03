'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { balanceService } from '@/services/balance'
import type { CreateFixedAssetInput } from '@/services/balance'

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

export function useFixedAssets(clientId: string, fiscalYearId: string) {
  return useQuery({
    queryKey: ['fixed-assets', clientId, fiscalYearId],
    queryFn: () => balanceService.listFixedAssets(clientId, fiscalYearId),
    enabled: !!clientId && !!fiscalYearId,
  })
}

export function useCreateFixedAsset(clientId: string, fiscalYearId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: CreateFixedAssetInput) =>
      balanceService.createFixedAsset(clientId, fiscalYearId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['fixed-assets', clientId, fiscalYearId] })
    },
  })
}

export function useDepreciate(clientId: string, fiscalYearId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (assetId: string) =>
      balanceService.depreciate(clientId, fiscalYearId, assetId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['fixed-assets', clientId, fiscalYearId] })
      queryClient.invalidateQueries({
        queryKey: ['depreciation-schedule', clientId, fiscalYearId],
      })
    },
  })
}

export function useDepreciationSchedule(
  clientId: string,
  fiscalYearId: string,
  assetId: string,
) {
  return useQuery({
    queryKey: ['depreciation-schedule', clientId, fiscalYearId, assetId],
    queryFn: () =>
      balanceService.getDepreciationSchedule(clientId, fiscalYearId, assetId),
    enabled: !!clientId && !!fiscalYearId && !!assetId,
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
