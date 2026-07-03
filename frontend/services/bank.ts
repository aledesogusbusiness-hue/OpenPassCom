import { apiClient } from '@/lib/api-client'
import type { BankStatement, BankTransaction, ReconciliationSummary } from '@/types'

export interface CreateBankStatementInput {
  iban: string
  data_inizio: string
  data_fine: string
  saldo_iniziale: string
  saldo_finale: string
  filename?: string
}

export interface ReconcileInput {
  journal_entry_id?: string
  scheduled_payment_id?: string
  note?: string
}

export const bankService = {
  listStatements(clientId: string): Promise<BankStatement[]> {
    return apiClient.get<BankStatement[]>(
      `/api/v1/clients/${clientId}/bank-statements`
    )
  },

  createStatement(clientId: string, data: CreateBankStatementInput): Promise<BankStatement> {
    return apiClient.post<BankStatement>(
      `/api/v1/clients/${clientId}/bank-statements`,
      data
    )
  },

  listTransactions(clientId: string, statementId: string): Promise<BankTransaction[]> {
    return apiClient.get<BankTransaction[]>(
      `/api/v1/clients/${clientId}/bank-statements/${statementId}/transactions`
    )
  },

  getSummary(clientId: string, statementId: string): Promise<ReconciliationSummary> {
    return apiClient.get<ReconciliationSummary>(
      `/api/v1/clients/${clientId}/bank-statements/${statementId}/summary`
    )
  },

  reconcile(
    clientId: string,
    statementId: string,
    transactionId: string,
    data: ReconcileInput
  ): Promise<BankTransaction> {
    return apiClient.post<BankTransaction>(
      `/api/v1/clients/${clientId}/bank-statements/${statementId}/transactions/${transactionId}/reconcile`,
      data
    )
  },

  markIrrilevante(
    clientId: string,
    statementId: string,
    transactionId: string
  ): Promise<BankTransaction> {
    return apiClient.post<BankTransaction>(
      `/api/v1/clients/${clientId}/bank-statements/${statementId}/transactions/${transactionId}/mark-irrilevante`,
      {}
    )
  },
}
