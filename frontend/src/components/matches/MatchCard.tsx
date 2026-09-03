import { ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'

import { StatusBadge } from '@/components/common/StatusBadge'
import { MatchScore } from '@/components/matches/MatchScore'
import { formatarData } from '@/lib/format'
import type { Match } from '@/types/api'

/**
 * Uma partida no histórico.
 *
 * Quem decide se há placar a exibir é este card, não o `MatchScore`: partida
 * agendada não tem resultado, e cancelada tem um resultado que não vale.
 */
export function MatchCard({ partida }: { partida: Match }) {
  const realizada = partida.status === 'PLAYED'
  const temPlacar = partida.team_1_score !== null && partida.team_2_score !== null

  return (
    <li>
      <Link
        to={`/partidas/${partida.id}`}
        className="flex flex-col gap-4 rounded-card border border-border bg-card p-5 transition-colors hover:border-primary/40"
      >
        <div className="flex items-center justify-between gap-3">
          <span className="tabular text-sm text-muted-foreground">
            {formatarData(partida.match_date)}
          </span>
          <StatusBadge status={partida.status} />
        </div>

        <div className="flex items-center justify-center gap-4 text-center">
          <span className="flex-1 font-display text-lg uppercase tracking-wide">
            {partida.team_1_name}
          </span>

          {realizada && temPlacar ? (
            <MatchScore home={partida.team_1_score!} away={partida.team_2_score!} />
          ) : (
            <span
              aria-hidden
              className={
                partida.status === 'CANCELLED'
                  ? 'font-display text-xl text-muted-foreground line-through'
                  : 'font-display text-xl text-muted-foreground'
              }
            >
              {partida.status === 'CANCELLED' && temPlacar
                ? `${partida.team_1_score} x ${partida.team_2_score}`
                : 'x'}
            </span>
          )}

          <span className="flex-1 font-display text-lg uppercase tracking-wide">
            {partida.team_2_name}
          </span>
        </div>

        <span className="flex items-center justify-center gap-2 text-label font-semibold uppercase text-primary-hi">
          Ver partida
          <ArrowRight aria-hidden className="h-4 w-4" />
        </span>
      </Link>
    </li>
  )
}
