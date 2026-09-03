import { api } from '@/api/client'
import { parametrosDoPeriodo } from '@/lib/period'
import type {
  MatchDetail,
  MatchList,
  MatchStatus,
  MatchWrite,
  PeriodSelection,
} from '@/types/api'

/** Uma página do histórico. */
export const PARTIDAS_POR_PAGINA = 10

export interface FiltroDeHistorico {
  status: MatchStatus | null
  periodo: PeriodSelection
}

export function listMatches(
  filtro: FiltroDeHistorico,
  offset: number,
): Promise<MatchList> {
  const parametros = [
    `limit=${PARTIDAS_POR_PAGINA}`,
    `offset=${offset}`,
    ...(filtro.status ? [`status=${filtro.status}`] : []),
    ...parametrosDoPeriodo(filtro.periodo),
  ]
  return api.get<MatchList>(`/matches?${parametros.join('&')}`)
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
