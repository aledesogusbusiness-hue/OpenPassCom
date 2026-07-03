'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { journalService } from '@/services/journal'
import type { CreateJournalEntryInput } from '@/services/journal'
import { triggerDownload } from '@/lib/utils'

export function useJournalEntries(clientId: string, fiscalYearId: string) {
  return useQuery({
    queryKey: ['journal-entries', clientId, fiscalYearId],
    queryFn: () => journalService.list(clientId, fiscalYearId),
    enabled: !!clientId && !!fiscalYearId,
  })
}

export function useJournalEntry(
  clientId: string,
  fiscalYearId: string,
  entryId: string,
) {
  return useQuery({
    queryKey: ['journal-entries', clientId, fiscalYearId, entryId],
    queryFn: () => journalService.get(clientId, fiscalYearId, entryId),
    enabled: !!clientId && !!fiscalYearId && !!entryId,
  })
}

export function useCreateJournalEntry(clientId: string, fiscalYearId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: CreateJournalEntryInput) =>
      journalService.create(clientId, fiscalYearId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['journal-entries', clientId, fiscalYearId],
      })
      queryClient.invalidateQueries({
        queryKey: ['bilancio-verifica', clientId, fiscalYearId],
      })
    },
  })
}

export function usePostJournalEntry(clientId: string, fiscalYearId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (entryId: string) =>
      journalService.post(clientId, fiscalYearId, entryId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['journal-entries', clientId, fiscalYearId],
      })
      queryClient.invalidateQueries({
        queryKey: ['bilancio-verifica', clientId, fiscalYearId],
      })
    },
  })
}

export function useReverseJournalEntry(clientId: string, fiscalYearId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (entryId: string) =>
      journalService.reverse(clientId, fiscalYearId, entryId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['journal-entries', clientId, fiscalYearId],
      })
      queryClient.invalidateQueries({
        queryKey: ['bilancio-verifica', clientId, fiscalYearId],
      })
    },
  })
}

export function useBilancioVerifica(clientId: string, fiscalYearId: string) {
  return useQuery({
    queryKey: ['bilancio-verifica', clientId, fiscalYearId],
    queryFn: () => journalService.getBilancioVerifica(clientId, fiscalYearId),
    enabled: !!clientId && !!fiscalYearId,
  })
}

export function useExportLibroGiornale(clientId: string, fiscalYearId: string) {
  return useMutation({
    mutationFn: async (format: 'pdf' | 'xlsx') => {
      const { blob, filename } = await journalService.exportLibroGiornale(clientId, fiscalYearId, format)
      triggerDownload(blob, filename)
    },
  })
}
