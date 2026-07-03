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

export interface UpdateTaskInput {
  titolo?: string
  descrizione?: string
  priorita?: string
  data_scadenza?: string
  assegnato_a?: string
  note?: string
}

export interface CreateConservatoreInput {
  tipo_documento: string
  fiscal_year_id?: string
  periodo?: string
  note?: string
}

export const studioService = {
  getDashboard(): Promise<DashboardSummary> {
    return apiClient.get<DashboardSummary>('/api/v1/dashboard')
  },

  listTasks(): Promise<StudioTask[]> {
    return apiClient.get<StudioTask[]>('/api/v1/tasks')
  },

  createTask(data: CreateTaskInput): Promise<StudioTask> {
    return apiClient.post<StudioTask>('/api/v1/tasks', data)
  },

  updateTask(taskId: string, data: UpdateTaskInput): Promise<StudioTask> {
    return apiClient.put<StudioTask>(`/api/v1/tasks/${taskId}`, data)
  },

  completeTask(taskId: string, completatoIl: string): Promise<StudioTask> {
    return apiClient.post<StudioTask>(`/api/v1/tasks/${taskId}/complete`, {
      completato_il: completatoIl,
    })
  },

  cancelTask(taskId: string): Promise<StudioTask> {
    return apiClient.post<StudioTask>(`/api/v1/tasks/${taskId}/cancel`, {})
  },

  listConservatore(clientId: string): Promise<ConservatoreLog[]> {
    return apiClient.get<ConservatoreLog[]>(
      `/api/v1/clients/${clientId}/conservatore-logs`
    )
  },

  createConservatore(clientId: string, data: CreateConservatoreInput): Promise<ConservatoreLog> {
    return apiClient.post<ConservatoreLog>(
      `/api/v1/clients/${clientId}/conservatore-logs`,
      data
    )
  },
}
