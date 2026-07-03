import { apiClient } from '@/lib/api-client'
import type { DashboardSummary, StudioTask, ConservatoreLog } from '@/types'

export interface CreateTaskInput {
  titolo: string
  tipo: string
  priorita?: string
  data_scadenza?: string
  client_entity_id?: string
  fiscal_year_id?: string
  descrizione?: string
}

export interface CreateConservatoreInput {
  tipo_documento: string
  fiscal_year_id?: string
  periodo?: string
  note?: string
}

export const studioService = {
  getDashboard(): Promise<DashboardSummary> {
    return apiClient.get<DashboardSummary>('/api/v1/studio/dashboard')
  },

  listTasks(): Promise<StudioTask[]> {
    return apiClient.get<StudioTask[]>('/api/v1/studio/tasks')
  },

  createTask(data: CreateTaskInput): Promise<StudioTask> {
    return apiClient.post<StudioTask>('/api/v1/studio/tasks', data)
  },

  updateTask(taskId: string, data: Partial<CreateTaskInput>): Promise<StudioTask> {
    return apiClient.patch<StudioTask>(`/api/v1/studio/tasks/${taskId}`, data)
  },

  listConservatore(clientId: string): Promise<ConservatoreLog[]> {
    return apiClient.get<ConservatoreLog[]>(
      `/api/v1/clients/${clientId}/conservatore`
    )
  },

  createConservatore(clientId: string, data: CreateConservatoreInput): Promise<ConservatoreLog> {
    return apiClient.post<ConservatoreLog>(
      `/api/v1/clients/${clientId}/conservatore`,
      data
    )
  },
}
