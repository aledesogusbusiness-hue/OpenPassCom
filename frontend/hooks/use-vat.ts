'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { vatService } from '@/services/vat'
import type { ElaborateFatturaPAInput, CreateVatEntryInput, CreateWithholdingInput } from '@/services/vat'

export function useVatEntries(clientId: string, fiscalYearId: string) {
  return useQuery({
    queryKey: ['vat-entries', clientId, fiscalYearId],
    queryFn: () => vatService.listEntries(clientId, fiscalYearId),
    enabled: !!clientId && !!fiscalYearId,
  })
}

export function useCreateVatEntry(clientId: string, fiscalYearId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: CreateVatEntryInput) =>
      vatService.createEntry(clientId, fiscalYearId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vat-entries', clientId, fiscalYearId] })
    },
  })
}

export function useVatSettlements(clientId: string, fiscalYearId: string) {
  return useQuery({
    queryKey: ['vat-settlements', clientId, fiscalYearId],
    queryFn: () => vatService.listSettlements(clientId, fiscalYearId),
    enabled: !!clientId && !!fiscalYearId,
  })
}

export function useCreateVatSettlement(clientId: string, fiscalYearId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: { periodo: string; credito_precedente?: string }) =>
      vatService.createSettlement(clientId, fiscalYearId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vat-settlements', clientId, fiscalYearId] })
    },
  })
}

export function useMarkSettlementVersata(
  clientId: string,
  fiscalYearId: string,
) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      settlementId,
      data,
    }: {
      settlementId: string
      data: { data_versamento: string; f24_riferimento?: string }
    }) => vatService.markSettlementVersata(clientId, fiscalYearId, settlementId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['vat-settlements', clientId, fiscalYearId],
      })
    },
  })
}

export function useWithholdingTaxes(clientId: string, fiscalYearId: string) {
  return useQuery({
    queryKey: ['withholding-taxes', clientId, fiscalYearId],
    queryFn: () => vatService.listWithholding(clientId, fiscalYearId),
    enabled: !!clientId && !!fiscalYearId,
  })
}

export function useCreateWithholding(clientId: string, fiscalYearId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: CreateWithholdingInput) =>
      vatService.createWithholding(clientId, fiscalYearId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['withholding-taxes', clientId, fiscalYearId] })
    },
  })
}

export function useMarkWithholdingVersata(
  clientId: string,
  fiscalYearId: string,
) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      withholdingId,
      data,
    }: {
      withholdingId: string
      data: { data_versamento: string; f24_riferimento?: string }
    }) =>
      vatService.markWithholdingVersata(clientId, fiscalYearId, withholdingId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['withholding-taxes', clientId, fiscalYearId],
      })
    },
  })
}

export function useFatturePa(clientId: string, fiscalYearId: string) {
  return useQuery({
    queryKey: ['fatture-pa', clientId, fiscalYearId],
    queryFn: () => vatService.listFatturePa(clientId, fiscalYearId),
    enabled: !!clientId && !!fiscalYearId,
  })
}

export function useUploadFatturaPA(clientId: string, fiscalYearId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (file: File) =>
      vatService.uploadFatturaPA(clientId, fiscalYearId, file),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['fatture-pa', clientId, fiscalYearId],
      })
    },
  })
}

export function useElaborateFatturaPA(clientId: string, fiscalYearId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ importId, data }: { importId: string; data: ElaborateFatturaPAInput }) =>
      vatService.elaborateFatturaPA(clientId, fiscalYearId, importId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['fatture-pa', clientId, fiscalYearId],
      })
    },
  })
}
