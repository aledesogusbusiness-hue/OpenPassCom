import { apiClient } from '@/lib/api-client'
import type { User } from '@/types'

export interface CreateUserInput {
  email: string
  password: string
  full_name: string
  role: 'admin' | 'accountant' | 'collaborator'
}

export interface UpdateUserInput {
  full_name?: string
  role?: 'admin' | 'accountant' | 'collaborator'
  is_active?: boolean
  password?: string
}

export interface ClientPermission {
  id: string
  studio_id: string
  user_id: string
  client_entity_id: string
  permesso: 'lettura' | 'scrittura'
  created_at: string
  created_by?: string
}

export const usersService = {
  list(includeInactive = false): Promise<User[]> {
    return apiClient.get<User[]>(`/api/v1/users?include_inactive=${includeInactive}`)
  },

  create(data: CreateUserInput): Promise<User> {
    return apiClient.post<User>('/api/v1/users', data)
  },

  update(userId: string, data: UpdateUserInput): Promise<User> {
    return apiClient.patch<User>(`/api/v1/users/${userId}`, data)
  },

  deactivate(userId: string): Promise<void> {
    return apiClient.delete<void>(`/api/v1/users/${userId}`)
  },

  listClientPermissions(clientId: string): Promise<ClientPermission[]> {
    return apiClient.get<ClientPermission[]>(`/api/v1/clients/${clientId}/permissions`)
  },

  grantPermission(
    clientId: string,
    userId: string,
    permesso: 'lettura' | 'scrittura'
  ): Promise<ClientPermission> {
    return apiClient.post<ClientPermission>(`/api/v1/clients/${clientId}/permissions`, {
      user_id: userId,
      permesso,
    })
  },

  revokePermission(clientId: string, userId: string): Promise<void> {
    return apiClient.delete<void>(`/api/v1/clients/${clientId}/permissions/${userId}`)
  },
}
