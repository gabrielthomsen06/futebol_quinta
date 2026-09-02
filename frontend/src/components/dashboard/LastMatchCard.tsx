import { Trophy } from 'lucide-react'

import { formatarData } from '@/lib/format'
import { cn } from '@/lib/utils'
import type { Match } from '@/types/api'

/**
 * A última partida realizada.
 *
 * Sem "Ver detalhes" nesta fase: `/partidas/:id` só existe de verdade na Fase
 * 10, e um botão que leva a um placeholder é pior que botão nenhum.
 */
export function LastMatchCard({ partida }: { partida: Match | null }) {
  return (
    <section className="rounded-card border border-border bg-card p-5">
      <h2 className="flex items-center gap-2 font-display text-section uppercase text-gold">
        <Trophy aria-hidden className="h-4 w-4" />
        Última partida
      </h2>

      {partida === null ? (
        <p className="mt-6 text-center text-muted-foreground">
          Nenhuma partida realizada ainda
        </p>
      ) : (
        <>
          <p className="mt-1 tabular text-sm text-muted-foreground">
            {formatarData(partida.match_date)}
          </p>
          <div className="mt-5 flex items-center justify-center gap-4 text-center">
            <span className="flex-1 font-display text-lg uppercase tracking-wide">
              {partida.team_1_name}
            </span>
            <span className="tabular font-display text-stat">
              <Placar valor={partida.team_1_score} vencedor={venceu(partida, 1)} />
              <span className="mx-2 text-lg text-muted-foreground">x</span>
              <Placar valor={partida.team_2_score} vencedor={venceu(partida, 2)} />
            </span>
            <span className="flex-1 font-display text-lg uppercase tracking-wide">
              {partida.team_2_name}
            </span>
          </div>
        </>
      )}
    </section>
  )
}

function venceu(partida: Match, time: 1 | 2): boolean {
  if (partida.team_1_score === null || partida.team_2_score === null) return false
  return time === 1
    ? partida.team_1_score > partida.team_2_score
    : partida.team_2_score > partida.team_1_score
}

function Placar({ valor, vencedor }: { valor: number | null; vencedor: boolean }) {
  return (
    <span className={cn(vencedor ? 'text-primary' : 'text-foreground')}>{valor ?? '-'}</span>
  )
}
