'use client'

import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { apiLogin, apiMe, apiRegister, getToken, setToken } from './api'

interface AuthUser {
  id: string
  email: string
  displayName: string | null
}

interface AuthContextValue {
  user: AuthUser | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, displayName?: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [loading, setLoading] = useState(true)

  // on mount, try to restore session from localStorage token
  useEffect(() => {
    const saved = localStorage.getItem('zici_token')
    if (!saved) { setLoading(false); return }
    setToken(saved)
    apiMe()
      .then(me => setUser({ id: me.id, email: me.email, displayName: me.display_name }))
      .catch(() => { localStorage.removeItem('zici_token'); setToken(null) })
      .finally(() => setLoading(false))
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    const token = await apiLogin(email, password)
    setToken(token)
    localStorage.setItem('zici_token', token)
    const me = await apiMe()
    setUser({ id: me.id, email: me.email, displayName: me.display_name })
  }, [])

  const register = useCallback(async (email: string, password: string, displayName?: string) => {
    await apiRegister(email, password, displayName)
    await login(email, password)
  }, [login])

  const logout = useCallback(() => {
    setToken(null)
    localStorage.removeItem('zici_token')
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
