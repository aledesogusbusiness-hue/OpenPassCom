import { apiClient } from '@/lib/api-client'
import type { ClientEntity, FiscalYear, AccountPlan, Account, AccountType } from '@/types'

export type CreateClientInput = {
  ragione_sociale: string
  codice_fiscale?: string
  partita_iva?: string
  fiscal_regime: 'ordinario' | 'semplificato' | 'forfettario'
  periodicita_iva?: 'mensile' | 'trimestrale'
  note?: string
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
    return apiClient.put<ClientEntity>(`/api/v1/clients/${id}`, data)
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

  closeFiscalYear(clientId: string, yearId: string): Promise<FiscalYear> {
    return apiClient.post<FiscalYear>(`/api/v1/clients/${clientId}/fiscal-years/${yearId}/close`, {})
  },

  getAccountPlan(clientId: string): Promise<AccountPlan> {
    return apiClient.get<AccountPlan>(`/api/v1/clients/${clientId}/account-plan`)
  },

  listAccounts(clientId: string, accountTypeId?: string): Promise<Account[]> {
    const query = accountTypeId ? `?account_type_id=${accountTypeId}` : ''
    return apiClient.get<Account[]>(`/api/v1/clients/${clientId}/accounts${query}`)
  },

  createAccount(
    clientId: string,
    data: { account_plan_id: string; account_type_id: string; codice: string; nome: string; livello?: number; parent_id?: string },
  ): Promise<Account> {
    return apiClient.post<Account>(`/api/v1/clients/${clientId}/accounts`, data)
  },

  listAccountTypes(): Promise<AccountType[]> {
    return apiClient.get<AccountType[]>('/api/v1/account-types')
  },
}
