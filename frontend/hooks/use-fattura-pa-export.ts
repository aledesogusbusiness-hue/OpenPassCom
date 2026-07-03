'use client'

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { fatturaPaExportService } from '@/services/fattura-pa-export'
import type { CreateFatturaPAExportInput } from '@/services/fattura-pa-export'
import { triggerDownload } from '@/lib/utils'

export function useFatturePaExport(clientId: string, fiscalYearId: string) {
  return useQuery({
    queryKey: ['fatture-pa-export', clientId, fiscalYearId],
    queryFn: () => fatturaPaExportService.list(clientId, fiscalYearId),
    enabled: !!clientId && !!fiscalYearId,
  })
}

export function useCreateFatturaPaExport(clientId: string, fiscalYearId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: CreateFatturaPAExportInput) =>
      fatturaPaExportService.create(clientId, fiscalYearId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['fatture-pa-export', clientId, fiscalYearId] })
    },
  })
}

export function useGenerateFatturaPaXml(clientId: string, fiscalYearId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (exportId: string) =>
      fatturaPaExportService.generateXml(clientId, fiscalYearId, exportId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['fatture-pa-export', clientId, fiscalYearId] })
    },
  })
}

export function useDownloadFatturaPaXml(clientId: string, fiscalYearId: string) {
  return useMutation({
    mutationFn: async (exportId: string) => {
      const { blob, filename } = await fatturaPaExportService.download(clientId, fiscalYearId, exportId)
      triggerDownload(blob, filename)
    },
  })
}

export function useMarkFatturaPaInviata(clientId: string, fiscalYearId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ exportId, identificativoSdi }: { exportId: string; identificativoSdi?: string }) =>
      fatturaPaExportService.markInviata(clientId, fiscalYearId, exportId, identificativoSdi),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['fatture-pa-export', clientId, fiscalYearId] })
    },
  })
}

export function useMarkFatturaPaEsito(clientId: string, fiscalYearId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      exportId,
      esito,
      messaggio,
    }: {
      exportId: string
      esito: 'accettata' | 'scartata' | 'consegnata'
      messaggio?: string
    }) => fatturaPaExportService.markEsito(clientId, fiscalYearId, exportId, esito, messaggio),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['fatture-pa-export', clientId, fiscalYearId] })
    },
  })
}
