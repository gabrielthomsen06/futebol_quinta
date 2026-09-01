import { useQueryClient } from '@tanstack/react-query'
import { createContext, useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'

import * as authApi from '@/api/auth'
import { clearToken, getToken, onUnauthorized, setToken } from '@/lib/session'
import type { AuthUser } from '@/types/api'

export interface AuthContextValue {
  user: AuthUser | null
  isAuthenticated: boolean
  /** Verdadeiro enquanto o token guardado ainda está sendo conferido. */
  isLoading: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => void
}

export const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()
  const [user, setUser] = useState<AuthUser | null>(null)
  // Começa carregando só se existe token para conferir; sem token, não há
  // nada a esperar.
  const [isLoading, setIsLoading] = useState(() => getToken() !== null)

  const encerrarSessao = useCallback(() => {
    clearToken()
    setUser(null)
    // Sem isso, dados carregados durante a sessão continuariam em cache.
    queryClient.clear()
  }, [queryClient])

  // O servidor recusou o token no meio do uso: derruba a sessão aqui também.
  useEffect(() => {
    onUnauthorized(() => {
      setUser(null)
      queryClient.clear()
    })
    return () => onUnauthorized(null)
  }, [queryClient])

  // No arranque, confere se o token guardado ainda vale. Enquanto isso o app
  // fica em carregando — sem essa espera, uma rota protegida piscaria a tela
  // de login antes de decidir.
  useEffect(() => {
    if (getToken() === null) {
      setIsLoading(false)
      return
    }

    let cancelado = false
    authApi
      .me()
      .then((autenticado) => {
        if (!cancelado) setUser(autenticado)
      })
      .catch(() => {
        if (!cancelado) clearToken()
      })
      .finally(() => {
        if (!cancelado) setIsLoading(false)
      })

    return () => {
      cancelado = true
    }
  }, [])

  const login = useCallback(async (username: string, password: string) => {
    const { access_token } = await authApi.login(username, password)
    setToken(access_token)
    try {
      setUser(await authApi.me())
    } catch (erro) {
      // Token que não serve para nada não vale a pena guardar.
      clearToken()
      throw erro
    }
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isAuthenticated: user !== null,
      isLoading,
      login,
      logout: encerrarSessao,
    }),
    [user, isLoading, login, encerrarSessao],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
