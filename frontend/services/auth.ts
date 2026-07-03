import { apiClient } from '@/lib/api-client'
import type { User } from '@/types'

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const authService = {
  async login(email: string, password: string): Promise<{ access_token: string; token_type: string }> {
    const res = await fetch(BASE_URL + '/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Credenziali non valide' }))
      throw new Error(typeof err.detail === 'string' ? err.detail : 'Credenziali non valide')
    }
    return res.json()
  },
  async getMe(): Promise<User> {
    return apiClient.get<User>('/api/v1/auth/me')
  },
}
