import { removeToken } from '@/lib/auth'
import type { ApiError } from '@/types'

class ApiClient {
  private baseUrl: string

  constructor() {
    this.baseUrl = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'
  }

  private getHeaders(): HeadersInit {
    const token = typeof window !== 'undefined' ? localStorage.getItem('openpasscom_token') : null
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
    return headers
  }

  private async handleResponse<T>(res: Response): Promise<T> {
    if (res.status === 401) {
      removeToken()
      if (typeof window !== 'undefined') {
        window.location.href = '/login'
      }
      throw new Error('Unauthorized')
    }
    if (!res.ok) {
      let detail: string
      try {
        const err = (await res.json()) as ApiError
        if (typeof err.detail === 'string') {
          detail = err.detail
        } else if (Array.isArray(err.detail)) {
          detail = err.detail.map((e) => e.msg).join('; ')
        } else {
          detail = `HTTP error ${res.status}`
        }
      } catch {
        detail = `HTTP error ${res.status}`
      }
      throw new Error(detail)
    }
    return res.json() as Promise<T>
  }

  async get<T>(path: string): Promise<T> {
    const res = await fetch(`${this.baseUrl}${path}`, {
      method: 'GET',
      headers: this.getHeaders(),
    })
    return this.handleResponse<T>(res)
  }

  async post<T>(path: string, body?: unknown): Promise<T> {
    const res = await fetch(`${this.baseUrl}${path}`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: body !== undefined ? JSON.stringify(body) : undefined,
    })
    return this.handleResponse<T>(res)
  }

  async patch<T>(path: string, body: unknown): Promise<T> {
    const res = await fetch(`${this.baseUrl}${path}`, {
      method: 'PATCH',
      headers: this.getHeaders(),
      body: JSON.stringify(body),
    })
    return this.handleResponse<T>(res)
  }

  async put<T>(path: string, body: unknown): Promise<T> {
    const res = await fetch(`${this.baseUrl}${path}`, {
      method: 'PUT',
      headers: this.getHeaders(),
      body: JSON.stringify(body),
    })
    return this.handleResponse<T>(res)
  }

  async delete<T>(path: string): Promise<T> {
    const res = await fetch(`${this.baseUrl}${path}`, {
      method: 'DELETE',
      headers: this.getHeaders(),
    })
    return this.handleResponse<T>(res)
  }

  async postForm<T>(path: string, formData: FormData): Promise<T> {
    const token = typeof window !== 'undefined' ? localStorage.getItem('openpasscom_token') : null
    const headers: Record<string, string> = {}
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
    const res = await fetch(`${this.baseUrl}${path}`, {
      method: 'POST',
      headers,
      body: formData,
    })
    return this.handleResponse<T>(res)
  }

  async postUrlEncoded<T>(path: string, params: Record<string, string>): Promise<T> {
    const token = typeof window !== 'undefined' ? localStorage.getItem('openpasscom_token') : null
    const headers: Record<string, string> = {
      'Content-Type': 'application/x-www-form-urlencoded',
    }
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
    const res = await fetch(`${this.baseUrl}${path}`, {
      method: 'POST',
      headers,
      body: new URLSearchParams(params).toString(),
    })
    return this.handleResponse<T>(res)
  }
}

export const apiClient = new ApiClient()
