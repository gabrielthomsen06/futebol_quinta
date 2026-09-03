import { Link } from 'react-router-dom'

import { PlayerAvatar } from '@/components/common/PlayerAvatar'
import type { MatchParticipation } from '@/types/api'

interface TeamLineupProps {
  nome: string
  placar: number | null
  jogadores: MatchParticipation[]
  /** Só partida realizada mostra gols e assistências. */
  mostrarEstatisticas: boolean
  vencedor: boolean
}

/**
 * A escalação de um time na página de detalhes.
 *
 * Cada jogador leva ao próprio perfil — o caminho de volta que, até esta fase,
 * só existia num sentido.
 */
export function TeamLineup({
  nome,
  placar,
  jogadores,
  mostrarEstatisticas,
  vencedor,
}: TeamLineupProps) {
  return (
    <section className="rounded-card border border-border bg-card p-5">
      <div className="mb-3 flex items-baseline justify-between gap-3 border-b border-border pb-3">
        <h2 className="font-display text-xl uppercase tracking-wide">{nome}</h2>
        {placar !== null && (
          <span
            className={`tabular font-display text-stat ${
              vencedor ? 'text-primary' : 'text-foreground'
            }`}
          >
            {placar}
          </span>
        )}
      </div>

      {jogadores.length === 0 ? (
        <p className="py-6 text-center text-sm text-muted-foreground">
          Ninguém escalado neste time.
        </p>
      ) : (
        <ul>
          {jogadores.map((jogador) => (
            <li key={jogador.player_id}>
              <Link
                to={`/jogadores/${jogador.player_id}`}
                className="flex items-center gap-3 border-b border-border py-3 transition-colors last:border-b-0 hover:text-primary-hi"
              >
                <PlayerAvatar
                  nickname={jogador.nickname}
                  photoPath={jogador.photo_path}
                  size="sm"
                />
                <span className="min-w-0 flex-1 truncate">{jogador.nickname}</span>
                {mostrarEstatisticas && (
                  <span className="tabular text-sm text-muted-foreground">
                    {jogador.goals} {jogador.goals === 1 ? 'gol' : 'gols'} ·{' '}
                    {jogador.assists} assist.
                  </span>
                )}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
