/**
 * Tipos que espelham os schemas Pydantic do backend.
 * Player, Match, Ranking e Dashboard entram junto com suas fases.
 */

export interface Health {
  status: 'ok' | 'degraded'
  database: 'ok' | 'erro'
  app: string
  version: string
  season: number
}
