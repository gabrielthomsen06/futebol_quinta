import { useQuery } from '@tanstack/react-query'

import { getHealth } from '@/api/health'
import { queryKeys } from '@/lib/queryClient'

/** Estado de conectividade com a API. Usado pelo indicador técnico da Fase 2. */
export function useHealth() {
  return useQuery({
    queryKey: queryKeys.health,
    queryFn: getHealth,
    staleTime: 15_000,
  })
}
