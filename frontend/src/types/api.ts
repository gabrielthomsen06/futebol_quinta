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

/** Enum do backend. Os rótulos em português são só apresentação. */
export type MatchStatus = 'SCHEDULED' | 'PLAYED' | 'CANCELLED'

export interface Match {
  id: string
  match_date: string
  status: MatchStatus
  team_1_name: string
  team_2_name: string
  team_1_score: number | null
  team_2_score: number | null
  created_at: string
  updated_at: string
}

export interface MatchParticipation {
  player_id: string
  nickname: string
  photo_path: string | null
  team: number
  goals: number
  assists: number
}

export interface MatchDetail extends Match {
  team_1: MatchParticipation[]
  team_2: MatchParticipation[]
}

export interface MatchList {
  items: Match[]
  total: number
  limit: number
  offset: number
}

/** Corpo de criação e edição. A escalação vai inteira, numa escrita só. */
export interface MatchWrite {
  match_date: string
  status: MatchStatus
  team_1_name: string
  team_2_name: string
  team_1_score: number | null
  team_2_score: number | null
  participants: {
    player_id: string
    team: 1 | 2
    goals: number
    assists: number
  }[]
}

export interface DashboardTotals {
  matches_played: number
  /** Soma dos gols individuais lançados, não dos placares. */
  goals_registered: number
  assists_registered: number
}

export interface GoalsPoint {
  match_date: string
  goals: number
}

export interface RankingEntry {
  position: number
  player: PlayerWithStats
}

export interface Dashboard {
  season: number
  totals: DashboardTotals
  /** Fora do filtro de temporada: é sobre o futuro. */
  next_match: Match | null
  /** Fora do filtro de temporada: interessa mesmo se foi na temporada passada. */
  last_match: Match | null
  top_scorers: RankingEntry[]
  top_assists: RankingEntry[]
  goals_timeline: GoalsPoint[]
}

export type RankingMetric =
  | 'goals'
  | 'assists'
  | 'wins'
  | 'games'
  | 'goals_per_game'
  | 'assists_per_game'

export interface Ranking {
  metric: RankingMetric
  /** Piso de partidas: 3 nas médias, 0 nas demais. A tela exibe, não recalcula. */
  min_games: number
  date_from: string | null
  date_to: string | null
  entries: RankingEntry[]
}

export interface Seasons {
  current: number
  /** Anos com partida em qualquer status, do mais recente ao mais antigo. */
  available: number[]
}

/** Recorte de período. Os três modos são mutuamente exclusivos no servidor. */
export type PeriodMode = 'season' | 'month' | 'range' | 'all'

export interface PeriodSelection {
  mode: PeriodMode
  season?: number
  month?: string
  dateFrom?: string
  dateTo?: string
}
