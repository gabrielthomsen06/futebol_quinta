import { Link } from 'react-router-dom'

import { PlayerAvatar } from '@/components/common/PlayerAvatar'
import { formatarMedia } from '@/lib/format'
import { cn } from '@/lib/utils'
import type { RankingEntry, RankingMetric } from '@/types/api'

/** O número principal, já formatado — médias com vírgula. */
function valorPrincipal(entrada: RankingEntry, metric: RankingMetric): string {
  const p = entrada.player
  switch (metric) {
    case 'goals':
      return String(p.goals)
    case 'assists':
      return String(p.assists)
    case 'wins':
      return String(p.wins)
    case 'games':
      return String(p.games)
    case 'goals_per_game':
      return formatarMedia(p.goals_per_game)
    case 'assists_per_game':
      return formatarMedia(p.assists_per_game)
  }
}

/** O dado de apoio: o que explica o número principal. */
function valorSecundario(entrada: RankingEntry, metric: RankingMetric): string {
  const p = entrada.player
  const jogos = `${p.games} ${p.games === 1 ? 'jogo' : 'jogos'}`
  switch (metric) {
    case 'goals_per_game':
      return `${jogos} · ${p.goals} ${p.goals === 1 ? 'gol' : 'gols'}`
    case 'assists_per_game':
      return `${jogos} · ${p.assists} assist.`
    case 'games':
      return `${p.wins}V ${p.draws}E ${p.losses}D`
    default:
      return jogos
  }
}

interface RankingItemProps {
  entrada: RankingEntry
  metric: RankingMetric
}

export function RankingItem({ entrada, metric }: RankingItemProps) {
  const lider = entrada.position === 1
  const inativo = entrada.player.status === 'INACTIVE'

  return (
    <li>
      <Link
        to={`/jogadores/${entrada.player.id}`}
        className={cn(
          'flex items-center gap-3 border-b border-border py-3 transition-colors last:border-b-0 hover:bg-card',
          lider && 'border-l-2 border-l-primary pl-3',
        )}
      >
        <span
          className={cn(
            'tabular w-7 text-center font-display text-lg font-extrabold',
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

        <div className="min-w-0 flex-1">
          <p className={cn('truncate', lider && 'font-semibold')}>
            {entrada.player.nickname}
            {inativo && (
              <span className="ml-2 text-label uppercase text-muted-foreground">inativo</span>
            )}
          </p>
          <p className="tabular text-xs text-muted-foreground">
            {valorSecundario(entrada, metric)}
          </p>
        </div>

        <span
          className={cn(
            'tabular font-display text-2xl font-extrabold',
            lider ? 'text-primary' : 'text-foreground',
          )}
        >
          {valorPrincipal(entrada, metric)}
        </span>
      </Link>
    </li>
  )
}
