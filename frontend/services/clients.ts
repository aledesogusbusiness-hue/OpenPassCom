import { apiClient } from '@/lib/api-client'
import type { ClientEntity, FiscalYear, AccountPlan, Account } from '@/types'

export type CreateClientInput = {
  ragione_sociale: string
  codice_fiscale: string
  partita_iva: string
  regime_fiscale: 'ordinario' | 'semplificato' | 'forfettario'
  email?: string
  pec?: string
  telefono?: string
  indirizzo?: string
  cap?: string
  citta?: string
  provincia?: string
}

export const clientsService = {
  list(): Promise<ClientEntity[]> {
    return apiClient.get<ClientEntity[]>('/api/v1/clients')
  },

  get(id: string): Promise<ClientEntity> {
    return apiClient.get<ClientEntity>(`/api/v1/clients/${id}`)
  },

  create(data: CreateClientInput): Promise<ClientEntity> {
    return apiClient.post<ClientEntity>('/api/v1/clients', data)
  },

  update(id: string, data: Partial<CreateClientInput>): Promise<ClientEntity> {
    return apiClient.patch<ClientEntity>(`/api/v1/clients/${id}`, data)
  },

  listFiscalYears(clientId: string): Promise<FiscalYear[]> {
    return apiClient.get<FiscalYear[]>(`/api/v1/clients/${clientId}/fiscal-years`)
  },

  createFiscalYear(
    clientId: string,
    data: { anno: number; data_inizio: string; data_fine: string },
  ): Promise<FiscalYear> {
    return apiClient.post<FiscalYear>(`/api/v1/clients/${clientId}/fiscal-years`, data)
  },

  listAccountPlans(clientId: string): Promise<AccountPlan[]> {
    return apiClient.get<AccountPlan[]>(`/api/v1/clients/${clientId}/account-plans`)
  },

  createAccountPlan(clientId: string, data: { nome: string }): Promise<AccountPlan> {
    return apiClient.post<AccountPlan>(`/api/v1/clients/${clientId}/account-plans`, data)
  },

  listAccounts(clientId: string, planId: string): Promise<Account[]> {
    return apiClient.get<Account[]>(`/api/v1/clients/${clientId}/account-plans/${planId}/accounts`)
  },

  createAccount(
    clientId: string,
    planId: string,
    data: { codice: string; nome: string; account_type_id: string; parent_id?: string },
  ): Promise<Account> {
    return apiClient.post<Account>(
      `/api/v1/clients/${clientId}/account-plans/${planId}/accounts`,
      data,
    )
  },
}
