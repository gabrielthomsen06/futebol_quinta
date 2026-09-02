import { CalendarDays } from 'lucide-react'

import { StatusBadge } from '@/components/common/StatusBadge'
import type { Match } from '@/types/api'

/** "qui, 11 de setembro" — o dia da semana importa numa pelada de quinta. */
function porExtenso(iso: string): string {
  const [ano, mes, dia] = iso.slice(0, 10).split('-').map(Number)
  // Construído como data local: `new Date(iso)` seria lido como UTC e, no
  // nosso fuso, exibiria o dia anterior.
  const data = new Date(ano, mes - 1, dia)
  return new Intl.DateTimeFormat('pt-BR', {
    weekday: 'short',
    day: 'numeric',
    month: 'long',
  }).format(data)
}

export function NextMatchCard({ partida }: { partida: Match | null }) {
  return (
    <section className="rounded-card border border-border bg-card p-5">
      <h2 className="flex items-center gap-2 font-display text-section uppercase text-gold">
        <CalendarDays aria-hidden className="h-4 w-4" />
        Próxima partida
      </h2>

      {partida === null ? (
        <p className="mt-6 text-center text-muted-foreground">Nenhuma partida agendada</p>
      ) : (
        <>
          <p className="mt-1 text-sm text-muted-foreground">{porExtenso(partida.match_date)}</p>
          <div className="mt-5 flex items-center justify-center gap-4 text-center">
            <span className="flex-1 font-display text-xl uppercase tracking-wide">
              {partida.team_1_name}
            </span>
            <span aria-hidden className="font-display text-lg text-muted-foreground">
              x
            </span>
            <span className="flex-1 font-display text-xl uppercase tracking-wide">
              {partida.team_2_name}
            </span>
          </div>
          <div className="mt-5 flex justify-center">
            <StatusBadge status={partida.status} />
          </div>
        </>
      )}
    </section>
  )
}
