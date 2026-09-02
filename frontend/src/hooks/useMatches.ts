import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import * as matchesApi from '@/api/matches'
import { invalidateDerivedData } from '@/lib/invalidate'
import { queryKeys } from '@/lib/queryClient'
import type { MatchWrite } from '@/types/api'

export function useMatches(limit = 50) {
  return useQuery({
    queryKey: queryKeys.matchList(`limit-${limit}`),
    queryFn: () => matchesApi.listMatches(limit),
  })
}

export function useMatch(id: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.match(id),
    queryFn: () => matchesApi.getMatch(id),
    enabled: enabled && id !== '',
  })
}

/**
 * Invalida partidas **e jogadores**.
 *
 * Mexer numa partida muda a estatística de todo mundo que jogou nela: gols,
 * jogos, vitórias. Invalidar só 'matches' deixaria a página de jogadores
 * mostrando número velho até o cache expirar.
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
