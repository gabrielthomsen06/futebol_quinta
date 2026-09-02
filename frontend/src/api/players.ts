import { api } from '@/api/client'
import type {
  Player,
  PlayerStatistics,
  PlayerStatus,
  PlayerStatusFilter,
  PlayerWithStats,
} from '@/types/api'

/**
 * Lista com estatísticas na mesma consulta.
 *
 * `with_stats=true` faz o backend devolver jogos, gols e assistências junto —
 * é o que o card precisa, sem uma segunda requisição por jogador.
 */
export function listPlayers(status: PlayerStatusFilter): Promise<PlayerWithStats[]> {
  return api.get<PlayerWithStats[]>(`/players?status=${status}&with_stats=true`)
}

export function getPlayerStats(id: string): Promise<PlayerStatistics> {
  return api.get<PlayerStatistics>(`/players/${id}/stats`)
}

// ---------------------------------------------------------------------------
// Escrita — exige administrador autenticado.
// Não existe remover jogador: quem sai do grupo é inativado.
// ---------------------------------------------------------------------------

export function createPlayer(nickname: string): Promise<Player> {
  return api.post<Player>('/players', { nickname })
}

export function updatePlayer(id: string, nickname: string): Promise<Player> {
  return api.put<Player>(`/players/${id}`, { nickname })
}

export function setPlayerStatus(id: string, status: PlayerStatus): Promise<Player> {
  return api.patch<Player>(`/players/${id}/status`, { status })
}

export function uploadPhoto(id: string, arquivo: File): Promise<Player> {
  const form = new FormData()
  form.append('foto', arquivo)
  return api.upload<Player>(`/players/${id}/photo`, form)
}

export function deletePhoto(id: string): Promise<Player> {
  return api.delete<Player>(`/players/${id}/photo`)
}
