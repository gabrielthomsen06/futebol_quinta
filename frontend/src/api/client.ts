/**
 * Cliente HTTP único da aplicação.
 *
 * Nenhum componente chama fetch direto: tudo passa por aqui, que centraliza a
 * URL base, o cabeçalho de autenticação e a normalização de erro.
 *
 * Como é passagem obrigatória, a expiração de sessão é tratada num lugar só:
 * qualquer 401 recebido com um token em mãos derruba a sessão.
 */

import { clearToken, getToken, notifyUnauthorized } from '@/lib/session'

const BASE_URL = import.meta.env.VITE_API_URL ?? '/api'

/** Erro vindo da API, já com a mensagem que o servidor mandou em "detail". */
export class ApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

type RequestOptions = Omit<RequestInit, 'body'> & { body?: unknown }

export async function apiFetch<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { body, headers, ...rest } = options
  const token = getToken()

  let response: Response
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      ...rest,
      headers: {
        ...(body !== undefined ? { 'Content-Type': 'application/json' } : {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...headers,
      },
      body: body !== undefined ? JSON.stringify(body) : undefined,
    })
  } catch {
    // Servidor fora do ar, rede caída, DNS: nunca chegou a haver resposta.
    throw new ApiError(0, 'Não foi possível falar com o servidor. Verifique sua conexão.')
  }

  if (response.status === 204) {
    return undefined as T
  }

  const payload: unknown = await response.json().catch(() => null)

  if (!response.ok) {
    const detail =
      payload && typeof payload === 'object' && 'detail' in payload
        ? String((payload as { detail: unknown }).detail)
        : `Erro ${response.status} ao chamar a API.`

    // Só derruba a sessão se havia token: o 401 do login com senha errada
    // não é sessão expirada.
    if (response.status === 401 && token) {
      clearToken()
      notifyUnauthorized()
    }

    throw new ApiError(response.status, detail)
  }

  return payload as T
}

export const api = {
  get: <T>(path: string) => apiFetch<T>(path),
  post: <T>(path: string, body?: unknown) => apiFetch<T>(path, { method: 'POST', body }),
  put: <T>(path: string, body?: unknown) => apiFetch<T>(path, { method: 'PUT', body }),
  patch: <T>(path: string, body?: unknown) => apiFetch<T>(path, { method: 'PATCH', body }),
  delete: <T>(path: string) => apiFetch<T>(path, { method: 'DELETE' }),
}
