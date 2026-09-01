import { api } from '@/api/client'
import type { Health } from '@/types/api'

export function getHealth(): Promise<Health> {
  return api.get<Health>('/health')
}
