import type { QueryClient } from '@tanstack/react-query'

import { queryKeys } from '@/lib/queryClient'

/**
 * Invalida tudo que é derivado das partidas.
 *
 * Nada de estatística é contador guardado: jogos, gols, vitórias e os números
 * do dashboard saem das partidas realizadas. Então mexer numa partida — ou
 * inativar um jogador — muda a tela de jogadores **e** a tela inicial.
 *
 * Fica numa função só de propósito. Espalhar essa lista pelos hooks é como se
 * esquece de invalidar alguma coisa: quando a Fase 9 acrescentar rankings,
 * muda-se aqui e mais nada.
 */
export function invalidateDerivedData(queryClient: QueryClient): Promise<unknown> {
  return Promise.all([
    queryClient.invalidateQueries({ queryKey: queryKeys.players }),
    queryClient.invalidateQueries({ queryKey: queryKeys.matches }),
    queryClient.invalidateQueries({ queryKey: queryKeys.dashboard }),
  ])
}
