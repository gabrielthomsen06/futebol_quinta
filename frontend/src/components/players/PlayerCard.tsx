import { Pencil, UserCheck, UserMinus } from 'lucide-react'
import { Link } from 'react-router-dom'

import { PlayerAvatar } from '@/components/common/PlayerAvatar'
import { Button } from '@/components/ui/button'
import type { PlayerWithStats } from '@/types/api'

interface PlayerCardProps {
  player: PlayerWithStats
  /** Controles de admin só aparecem para quem está autenticado. */
  isAdmin: boolean
  onEdit: (player: PlayerWithStats) => void
  onToggleStatus: (player: PlayerWithStats) => void
  pending?: boolean
}

/**
 * O jogador como personagem: foto, apelido e os três números que importam.
 *
 * Os números vêm de partidas realizadas — agendadas e canceladas não contam.
 */
export function PlayerCard({
  player,
  isAdmin,
  onEdit,
  onToggleStatus,
  pending = false,
}: PlayerCardProps) {
  const inativo = player.status === 'INACTIVE'

  return (
    <article className="flex flex-col items-center gap-4 rounded-card border border-border bg-card p-6">
      <div className="relative">
        <PlayerAvatar nickname={player.nickname} photoPath={player.photo_path} size="lg" />
        {inativo && (
          <span className="absolute -bottom-1 left-1/2 -translate-x-1/2 rounded-control border border-border bg-background px-2 py-0.5 text-label font-semibold uppercase text-muted-foreground">
            Inativo
          </span>
        )}
      </div>

      <h2 className="font-display text-2xl font-extrabold uppercase tracking-wide">
        {player.nickname}
      </h2>

      <dl className="grid w-full grid-cols-3 gap-2 border-y border-border py-4 text-center">
        <div>
          <dd className="tabular font-display text-stat text-primary">{player.games}</dd>
          <dt className="text-label font-semibold uppercase text-muted-foreground">Jogos</dt>
        </div>
        <div>
          <dd className="tabular font-display text-stat text-primary">{player.goals}</dd>
          <dt className="text-label font-semibold uppercase text-muted-foreground">Gols</dt>
        </div>
        <div>
          <dd className="tabular font-display text-stat text-primary">{player.assists}</dd>
          <dt className="text-label font-semibold uppercase text-muted-foreground">Assist.</dt>
        </div>
      </dl>

      <Button asChild variant="outline" className="w-full">
        <Link to={`/jogadores/${player.id}`}>Ver perfil</Link>
      </Button>

      {isAdmin && (
        <div className="flex w-full gap-2">
          <Button
            variant="ghost"
            size="sm"
            className="flex-1"
            onClick={() => onEdit(player)}
            disabled={pending}
          >
            <Pencil aria-hidden />
            Editar
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="flex-1"
            onClick={() => onToggleStatus(player)}
            disabled={pending}
          >
            {inativo ? <UserCheck aria-hidden /> : <UserMinus aria-hidden />}
            {inativo ? 'Ativar' : 'Inativar'}
          </Button>
        </div>
      )}
    </article>
  )
}
