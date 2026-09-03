import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import * as matchesApi from '@/api/matches'
import { PARTIDAS_POR_PAGINA, type FiltroDeHistorico } from '@/api/matches'
import { invalidateDerivedData } from '@/lib/invalidate'
import { chaveDoPeriodo } from '@/lib/period'
import { queryKeys } from '@/lib/queryClient'
import type { MatchWrite } from '@/types/api'

/**
 * O histórico, paginado por "carregar mais".
 *
 * **A chave carrega status e período.** Sem os dois, "Realizadas de agosto" e
 * "Todas de 2026" compartilhariam as mesmas páginas em cache e a segunda tela
 * mostraria os itens da primeira. Como a chave muda junto com o filtro, trocar
 * de filtro é outra query — que começa naturalmente em offset 0.
 */
export function useMatchHistory(filtro: FiltroDeHistorico) {
  return useInfiniteQuery({
    queryKey: queryKeys.matchList(
      `${filtro.status ?? 'todas'}:${chaveDoPeriodo(filtro.periodo)}`,
    ),
    queryFn: ({ pageParam }) => matchesApi.listMatches(filtro, pageParam),
    initialPageParam: 0,
    getNextPageParam: (ultima, todas) => {
      const carregadas = todas.reduce((soma, p) => soma + p.items.length, 0)
      // Para quando alcançar o total **deste** filtro.
      return carregadas < ultima.total ? carregadas : undefined
    },
  })
}

export { PARTIDAS_POR_PAGINA }

export function useMatch(id: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.match(id),
    queryFn: () => matchesApi.getMatch(id),
    enabled: enabled && id !== '',
  })
}

/**
 * Invalida partidas, jogadores, dashboard e rankings.
 *
 * Mexer numa partida muda a estatística de todo mundo que jogou nela.
 */
function useInvalidarPartidas() {
  const queryClient = useQueryClient()
  return () => invalidateDerivedData(queryClient)
}

export function useCreateMatch() {
  const invalidar = useInvalidarPartidas()
  return useMutation({
    mutationFn: (dados: MatchWrite) => matchesApi.createMatch(dados),
    onSuccess: invalidar,
  })
}

export function useUpdateMatch() {
  const invalidar = useInvalidarPartidas()
  return useMutation({
    mutationFn: ({ id, dados }: { id: string; dados: MatchWrite }) =>
      matchesApi.updateMatch(id, dados),
    onSuccess: invalidar,
  })
}

export function useDeleteMatch() {
  const invalidar = useInvalidarPartidas()
  return useMutation({
    mutationFn: (id: string) => matchesApi.deleteMatch(id),
    onSuccess: invalidar,
  })
}
