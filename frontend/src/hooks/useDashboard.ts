import { useQuery } from '@tanstack/react-query'

import { getDashboard } from '@/api/dashboard'
import { queryKeys } from '@/lib/queryClient'

export function useDashboard(season?: number) {
  return useQuery({
    queryKey: [...queryKeys.dashboard, season ?? 'atual'],
    queryFn: () => getDashboard(season),
  })
}
