import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import * as playersApi from '@/api/players'
import { invalidateDerivedData } from '@/lib/invalidate'
import { queryKeys } from '@/lib/queryClient'
import type { PlayerStatus, PlayerStatusFilter } from '@/types/api'

export function usePlayers(status: PlayerStatusFilter) {
  return useQuery({
    queryKey: queryKeys.playerList(status),
    queryFn: () => playersApi.listPlayers(status),
  })
}

export function usePlayerStats(id: string) {
  return useQuery({
    queryKey: queryKeys.playerStats(id),
    queryFn: () => playersApi.getPlayerStats(id),
  })
}

/**
 * Invalida tudo que é de jogador depois de uma escrita.
 *
 * Todas as chaves começam com 'players', então um único invalidate atinge a
 * listagem em qualquer filtro e os perfis abertos — sem precisar lembrar de
 * cada combinação.
 */
function useInvalidarJogadores() {
  const queryClient = useQueryClient()
  return () => invalidateDerivedData(queryClient)
}

export function useCreatePlayer() {
  const invalidar = useInvalidarJogadores()
  return useMutation({
    mutationFn: (nickname: string) => playersApi.createPlayer(nickname),
    onSuccess: invalidar,
  })
}

export function useUpdatePlayer() {
  const invalidar = useInvalidarJogadores()
  return useMutation({
    mutationFn: ({ id, nickname }: { id: string; nickname: string }) =>
      playersApi.updatePlayer(id, nickname),
    onSuccess: invalidar,
  })
}

export function useSetPlayerStatus() {
  const invalidar = useInvalidarJogadores()
  return useMutation({
    mutationFn: ({ id, status }: { id: string; status: PlayerStatus }) =>
      playersApi.setPlayerStatus(id, status),
    onSuccess: invalidar,
  })
}

export function useUploadPhoto() {
  const invalidar = useInvalidarJogadores()
  return useMutation({
    mutationFn: ({ id, arquivo }: { id: string; arquivo: File }) =>
      playersApi.uploadPhoto(id, arquivo),
    onSuccess: invalidar,
  })
}

export function useDeletePhoto() {
  const invalidar = useInvalidarJogadores()
  return useMutation({
    mutationFn: (id: string) => playersApi.deletePhoto(id),
    onSuccess: invalidar,
  })
}
