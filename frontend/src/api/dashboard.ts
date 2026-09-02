import { api } from '@/api/client'
import type { Dashboard } from '@/types/api'

/**
 * Tudo da tela inicial numa requisição.
 *
 * O backend executa várias consultas internamente, mas quem abre o site no
 * celular faz uma chamada de rede só.
 */
export function getDashboard(season?: number): Promise<Dashboard> {
  return api.get<Dashboard>(season ? `/dashboard?season=${season}` : '/dashboard')
}
