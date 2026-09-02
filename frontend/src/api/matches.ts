import { api } from '@/api/client'
import type { MatchDetail, MatchList, MatchWrite } from '@/types/api'

export function listMatches(limit = 50): Promise<MatchList> {
  return api.get<MatchList>(`/matches?limit=${limit}`)
}

export function getMatch(id: string): Promise<MatchDetail> {
  return api.get<MatchDetail>(`/matches/${id}`)
}

// ---------------------------------------------------------------------------
// Escrita — exige administrador autenticado.
// ---------------------------------------------------------------------------

export function createMatch(dados: MatchWrite): Promise<MatchDetail> {
  return api.post<MatchDetail>('/matches', dados)
}

/** Substitui a partida inteira, escalação inclusa, numa transação só. */
export function updateMatch(id: string, dados: MatchWrite): Promise<MatchDetail> {
  return api.put<MatchDetail>(`/matches/${id}`, dados)
}

export function deleteMatch(id: string): Promise<void> {
  return api.delete<void>(`/matches/${id}`)
}
