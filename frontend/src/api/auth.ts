import { api } from '@/api/client'
import type { AuthUser, LoginResponse } from '@/types/api'

export function login(username: string, password: string): Promise<LoginResponse> {
  return api.post<LoginResponse>('/auth/login', { username, password })
}

/** Confirma que o token guardado ainda vale e diz quem é o autenticado. */
export function me(): Promise<AuthUser> {
  return api.get<AuthUser>('/auth/me')
}
