import { useContext } from 'react'

import { AuthContext, type AuthContextValue } from '@/contexts/AuthContext'

export function useAuth(): AuthContextValue {
  const contexto = useContext(AuthContext)
  if (contexto === null) {
    throw new Error('useAuth precisa estar dentro de <AuthProvider>.')
  }
  return contexto
}
