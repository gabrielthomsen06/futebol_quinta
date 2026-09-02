import { useQuery } from '@tanstack/react-query'

import { getRanking, getSeasons } from '@/api/rankings'
import { queryKeys } from '@/lib/queryClient'
import type { PeriodSelection, RankingMetric } from '@/types/api'

/** Assinatura estável do período, para virar chave de cache. */
function chaveDoPeriodo(periodo: PeriodSelection): string {
  switch (periodo.mode) {
    case 'season':
      return `season:${periodo.season ?? ''}`
    case 'month':
      return `month:${periodo.month ?? ''}`
    case 'range':
      return `range:${periodo.dateFrom ?? ''}:${periodo.dateTo ?? ''}`
    case 'all':
      return 'all'
  }
}

export function useRanking(metric: RankingMetric, periodo: PeriodSelection) {
  return useQuery({
    queryKey: queryKeys.ranking(metric, chaveDoPeriodo(periodo)),
    queryFn: () => getRanking(metric, periodo),
  })
}

export function useSeasons() {
  return useQuery({
    queryKey: queryKeys.seasons,
    queryFn: getSeasons,
    // A lista de temporadas muda no máximo uma vez por ano.
    staleTime: 10 * 60_000,
  })
}
