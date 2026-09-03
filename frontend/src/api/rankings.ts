import { api } from '@/api/client'
import { parametrosDoPeriodo } from '@/lib/period'
import type { PeriodSelection, Ranking, RankingMetric, Seasons } from '@/types/api'

/** A lista completa pede 100; não há paginação. */
export const LIMITE_DO_RANKING = 100

export function getRanking(
  metric: RankingMetric,
  periodo: PeriodSelection,
): Promise<Ranking> {
  const parametros = [
    `metric=${metric}`,
    `limit=${LIMITE_DO_RANKING}`,
    ...parametrosDoPeriodo(periodo),
  ]
  return api.get<Ranking>(`/rankings?${parametros.join('&')}`)
}

export function getSeasons(): Promise<Seasons> {
  return api.get<Seasons>('/seasons')
}
