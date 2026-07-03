'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { clientsService } from '@/services/clients'
import type { CreateClientInput } from '@/services/clients'

export function useClients() {
  return useQuery({
    queryKey: ['clients'],
    queryFn: () => clientsService.list(),
  })
}

export function useClient(id: string) {
  return useQuery({
    queryKey: ['clients', id],
    queryFn: () => clientsService.get(id),
    enabled: !!id,
  })
}

export function useFiscalYears(clientId: string) {
  return useQuery({
    queryKey: ['fiscal-years', clientId],
    queryFn: () => clientsService.listFiscalYears(clientId),
    enabled: !!clientId,
  })
}

export function useCreateClient() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: CreateClientInput) => clientsService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clients'] })
    },
  })
}

export function useUpdateClient(id: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: Partial<CreateClientInput>) => clientsService.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clients'] })
      queryClient.invalidateQueries({ queryKey: ['clients', id] })
    },
  })
}

export function useCreateFiscalYear(clientId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: { anno: number; data_inizio: string; data_fine: string }) =>
      clientsService.createFiscalYear(clientId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['fiscal-years', clientId] })
    },
  })
}

export function useAccountPlan(clientId: string) {
  return useQuery({
    queryKey: ['account-plan', clientId],
    queryFn: () => clientsService.getAccountPlan(clientId),
    enabled: !!clientId,
  })
}

export function useAccounts(clientId: string) {
  return useQuery({
    queryKey: ['accounts', clientId],
    queryFn: () => clientsService.listAccounts(clientId),
    enabled: !!clientId,
  })
}

export function useAccountTypes() {
  return useQuery({
    queryKey: ['account-types'],
    queryFn: () => clientsService.listAccountTypes(),
    staleTime: 1000 * 60 * 60,
  })
}

export function useCreateAccount(clientId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: { account_plan_id: string; account_type_id: string; codice: string; nome: string; livello?: number; parent_id?: string }) =>
      clientsService.createAccount(clientId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts', clientId] })
    },
  })
}
