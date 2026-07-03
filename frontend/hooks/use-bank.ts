'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { bankService } from '@/services/bank'
import type { CreateBankStatementInput, ReconcileInput } from '@/services/bank'

export function useBankStatements(clientId: string) {
  return useQuery({
    queryKey: ['bank-statements', clientId],
    queryFn: () => bankService.listStatements(clientId),
    enabled: !!clientId,
  })
}

export function useCreateBankStatement(clientId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: CreateBankStatementInput) =>
      bankService.createStatement(clientId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bank-statements', clientId] })
    },
  })
}

export function useBankTransactions(clientId: string, statementId: string) {
  return useQuery({
    queryKey: ['bank-transactions', clientId, statementId],
    queryFn: () => bankService.listTransactions(clientId, statementId),
    enabled: !!clientId && !!statementId,
  })
}

export function useReconcileTransaction(clientId: string, statementId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      transactionId,
      data,
    }: {
      transactionId: string
      data: ReconcileInput
    }) => bankService.reconcile(clientId, statementId, transactionId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['bank-transactions', clientId, statementId],
      })
    },
  })
}

export function useMarkIrrilevante(clientId: string, statementId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (transactionId: string) =>
      bankService.markIrrilevante(clientId, statementId, transactionId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['bank-transactions', clientId, statementId],
      })
    },
  })
}
