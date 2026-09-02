import type { LucideIcon } from 'lucide-react'
import { Link } from 'react-router-dom'

import { PlayerAvatar } from '@/components/common/PlayerAvatar'
import { cn } from '@/lib/utils'
import type { RankingEntry } from '@/types/api'

interface TopPlayersListProps {
  title: string
  icon: LucideIcon
  entries: RankingEntry[]
  /** Qual número mostrar à direita. */
  metric: 'goals' | 'assists'
  emptyMessage: string
}

/**
 * Top 5 de uma métrica, no formato de lista.
 *
 * O primeiro colocado ganha destaque — número em laranja e uma barra na
 * lateral —, como nas telas de referência. Do segundo em diante o peso vai
 * caindo, para a leitura ter hierarquia sem precisar de cor nova.
 */
export function TopPlayersList({
  title,
  icon: Icon,
  entries,
  metric,
  emptyMessage,
}: TopPlayersListProps) {
  return (
    <section className="rounded-card border border-border bg-card p-5">
      <h2 className="flex items-center gap-2 font-display text-section uppercase text-gold">
        <Icon aria-hidden className="h-4 w-4" />
        {title}
      </h2>

      {entries.length === 0 ? (
        <p className="mt-6 text-center text-muted-foreground">{emptyMessage}</p>
      ) : (
        <ol className="mt-3">
          {entries.map((entrada) => {
            const lider = entrada.position === 1
            return (
              <li key={entrada.player.id}>
                <Link
                  to={`/jogadores/${entrada.player.id}`}
                  className={cn(
                    'flex items-center gap-3 border-b border-border py-3 last:border-b-0',
                    lider && 'border-l-2 border-l-primary pl-3',
                  )}
                >
                  <span
                    className={cn(
                      'tabular w-5 text-center font-display text-lg font-extrabold',
                      lider ? 'text-primary' : 'text-muted-foreground',
                    )}
                  >
                    {entrada.position}
                  </span>
                  <PlayerAvatar
                    nickname={entrada.player.nickname}
                    photoPath={entrada.player.photo_path}
                    size="sm"
                  />
                  <span
                    className={cn(
                      'min-w-0 flex-1 truncate',
                      lider ? 'font-semibold' : 'text-muted-foreground',
                    )}
                  >
                    {entrada.player.nickname}
                  </span>
                  <span
                    className={cn(
                      'tabular font-display text-xl font-extrabold',
                      lider ? 'text-primary' : 'text-foreground',
                    )}
                  >
                    {entrada.player[metric]}
                  </span>
                </Link>
              </li>
            )
          })}
        </ol>
      )}
    </section>
  )
}
