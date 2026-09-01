/**
 * Guarda do token, fora do React.
 *
 * O cliente HTTP precisa do token e o contexto de autenticação precisa saber
 * quando a sessão cai. Se um importasse o outro haveria ciclo, então os dois
 * conversam por aqui.
 *
 * Todo acesso ao localStorage é protegido: em janela anônima ou com dados de
 * site bloqueados, ler ou escrever pode lançar exceção.
 */

const CHAVE = 'migue.token'

let aoPerderSessao: (() => void) | null = null

export function getToken(): string | null {
  try {
    return localStorage.getItem(CHAVE)
  } catch {
    return null
  }
}

export function setToken(token: string): void {
  try {
    localStorage.setItem(CHAVE, token)
  } catch {
    // Sem persistência a sessão dura só enquanto a aba estiver aberta.
  }
}

export function clearToken(): void {
  try {
    localStorage.removeItem(CHAVE)
  } catch {
    // Nada a fazer.
  }
}

/** Registra o que acontece quando o servidor recusa o token. */
export function onUnauthorized(callback: (() => void) | null): void {
  aoPerderSessao = callback
}

export function notifyUnauthorized(): void {
  aoPerderSessao?.()
}
