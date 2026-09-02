import { PlayerAvatar } from '@/components/common/PlayerAvatar'
import { Button } from '@/components/ui/button'
import type { PlayerWithStats } from '@/types/api'

interface PlayerPickerProps {
  disponiveis: PlayerWithStats[]
  nomeTime1: string
  nomeTime2: string
  incluirInativos: boolean
  onIncluirInativos: (incluir: boolean) => void
  onEscalar: (player: PlayerWithStats, team: 1 | 2) => void
}

/**
 * Quem ainda não foi escalado.
 *
 * Dois botões por linha em vez de arrastar: no celular, tocar num botão é
 * confiável e arrastar não é. São dois toques no máximo por jogador.
 *
 * Inativos ficam escondidos por padrão — eles não entram na próxima partida —,
 * mas o botão os revela para o caso de alguém voltar a jogar.
 */
export function PlayerPicker({
  disponiveis,
  nomeTime1,
  nomeTime2,
  incluirInativos,
  onIncluirInativos,
  onEscalar,
}: PlayerPickerProps) {
  return (
    <section className="rounded-card border border-border bg-card p-4">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h2 className="font-display text-section uppercase text-gold">Disponíveis</h2>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          aria-pressed={incluirInativos}
          onClick={() => onIncluirInativos(!incluirInativos)}
        >
          {incluirInativos ? 'Ocultar inativos' : 'Incluir inativos'}
        </Button>
      </div>

      {disponiveis.length === 0 ? (
        <p className="rounded-control border border-dashed border-border px-4 py-6 text-center text-sm text-muted-foreground">
          Todos os jogadores já estão escalados.
        </p>
      ) : (
        <ul className="flex flex-col">
          {disponiveis.map((player) => (
            <li
              key={player.id}
              className="flex flex-wrap items-center gap-3 border-b border-border py-3 last:border-b-0"
            >
              <PlayerAvatar nickname={player.nickname} photoPath={player.photo_path} size="sm" />
              <span className="min-w-0 flex-1 truncate font-medium">
                {player.nickname}
                {player.status === 'INACTIVE' && (
                  <span className="ml-2 text-label uppercase text-muted-foreground">inativo</span>
                )}
              </span>
              <div className="flex gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => onEscalar(player, 1)}
                  aria-label={`Escalar ${player.nickname} no time ${nomeTime1}`}
                >
                  {nomeTime1 || 'Time 1'}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => onEscalar(player, 2)}
                  aria-label={`Escalar ${player.nickname} no time ${nomeTime2}`}
                >
                  {nomeTime2 || 'Time 2'}
                </Button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
