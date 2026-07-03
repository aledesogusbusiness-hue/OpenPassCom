'use client'

import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from 'react'
import {
  getToken,
  setToken,
  removeToken,
  getUser,
  setUser,
} from '@/lib/auth'
import type { User } from '@/types'

interface AuthContextValue {
  user: User | null
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUserState] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    async function initAuth() {
      const token = getToken()
      const cachedUser = getUser()

      if (!token) {
        setIsLoading(false)
        return
      }

      // Optimistically set cached user while verifying
      if (cachedUser) {
        setUserState(cachedUser)
      }

      try {
        const response = await fetch('/api/v1/auth/me', {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        })

        if (response.status === 401) {
          removeToken()
          localStorage.removeItem('user')
          setUserState(null)
        } else if (response.ok) {
          const verifiedUser: User = await response.json()
          setUser(verifiedUser)
          setUserState(verifiedUser)
        }
      } catch {
        // Network error — keep cached user if available
      } finally {
        setIsLoading(false)
      }
    }

    initAuth()
  }, [])

  async function login(email: string, password: string): Promise<void> {
    const body = new URLSearchParams({ username: email, password })

    const loginResponse = await fetch('/api/v1/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: body.toString(),
    })

    if (!loginResponse.ok) {
      const error = await loginResponse.json().catch(() => ({}))
      throw new Error(error?.detail ?? 'Login failed')
    }

    const { access_token } = await loginResponse.json()
    setToken(access_token)

    const meResponse = await fetch('/api/v1/auth/me', {
      headers: {
        Authorization: `Bearer ${access_token}`,
      },
    })

    if (!meResponse.ok) {
      throw new Error('Failed to fetch user profile')
    }

    const profile: User = await meResponse.json()
    setUser(profile)
    setUserState(profile)
  }

  function logout(): void {
    removeToken()
    localStorage.removeItem('user')
    setUserState(null)
    window.location.href = '/login'
  }

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
