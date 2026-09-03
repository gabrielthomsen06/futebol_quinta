import { useQuery } from '@tanstack/react-query'

import { getRanking, getSeasons } from '@/api/rankings'
import { chaveDoPeriodo } from '@/lib/period'
import { queryKeys } from '@/lib/queryClient'
import type { PeriodSelection, RankingMetric } from '@/types/api'

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
