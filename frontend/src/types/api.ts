/** Tipos que espelham os schemas Pydantic do backend. */

export interface Health {
  status: 'ok' | 'degraded'
  database: 'ok' | 'erro'
  app: string
  version: string
  season: number
}

export interface AuthUser {
  id: string
  username: string
}

export interface LoginResponse {
  access_token: string
  token_type: 'bearer'
  /** ISO 8601. O backend manda pronto para o frontend não decodificar o JWT. */
  expires_at: string
}

export type PlayerStatus = 'ACTIVE' | 'INACTIVE'

export interface Player {
  id: string
  nickname: string
  /** Caminho relativo, ex.: players/uuid-a1b2c3d4.webp. Nulo = sem foto. */
  photo_path: string | null
  status: PlayerStatus
  created_at: string
  updated_at: string
}

/**
 * Jogador com as estatísticas derivadas.
 *
 * Nada disto é contador guardado: sai de uma consulta agregada sobre as
 * partidas realizadas, toda vez.
 */
export interface PlayerWithStats {
  id: string
  nickname: string
  photo_path: string | null
  status: PlayerStatus
  games: number
  goals: number
  assists: number
  wins: number
  draws: number
  losses: number
  goals_per_game: number
  assists_per_game: number
  /** De 0 a 100. */
  win_rate: number
  goal_participations: number
}

export interface PlayerMatch {
  match_id: string
  match_date: string
  team_1_name: string
  team_2_name: string
  team_1_score: number
  team_2_score: number
  /** Lado em que o jogador estava: 1 ou 2. */
  team: number
  goals: number
  assists: number
  /** Do ponto de vista do jogador. */
  result: 'V' | 'E' | 'D'
}

export interface PlayerStatistics {
  stats: PlayerWithStats
  history: PlayerMatch[]
}

/** Filtro da listagem. O padrão do backend é só ativos. */
export type PlayerStatusFilter = 'active' | 'inactive' | 'all'
