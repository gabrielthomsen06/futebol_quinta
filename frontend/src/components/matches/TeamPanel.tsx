import { ParticipantRow, type Escalado } from '@/components/matches/ParticipantRow'
import { Input } from '@/components/ui/input'

interface TeamPanelProps {
  team: 1 | 2
  nome: string
  onNomeChange: (nome: string) => void
  placar: number | null
  onPlacarChange: (placar: number | null) => void
  escalados: Escalado[]
  mostrarEstatisticas: boolean
  /** Placar só é exigido em partida realizada. */
  exigirPlacar: boolean
  onParticipanteChange: (playerId: string, campo: 'goals' | 'assists', valor: number) => void
  onRemover: (playerId: string) => void
}

/**
 * Um lado da partida: nome livre, placar e quem jogou.
 *
 * O nome é editável porque time não é entidade — "BRANCO" desta quinta não tem
 * relação com o "BRANCO" de três meses atrás.
 */
export function TeamPanel({
  team,
  nome,
  onNomeChange,
  placar,
  onPlacarChange,
  escalados,
  mostrarEstatisticas,
  exigirPlacar,
  onParticipanteChange,
  onRemover,
}: TeamPanelProps) {
  const somaDeGols = escalados.reduce((total, e) => total + e.goals, 0)

  return (
    <section className="rounded-card border border-border bg-card p-4">
      <div className="flex items-end gap-3">
        <div className="flex min-w-0 flex-1 flex-col gap-1">
          <label
            htmlFor={`nome-time-${team}`}
            className="text-label font-semibold uppercase text-muted-foreground"
          >
            Nome do time {team}
          </label>
          <Input
            id={`nome-time-${team}`}
            value={nome}
            onChange={(e) => onNomeChange(e.target.value)}
            maxLength={40}
            required
          />
        </div>

        <div className="flex w-24 flex-col gap-1">
          <label
            htmlFor={`placar-time-${team}`}
            className="text-label font-semibold uppercase text-muted-foreground"
          >
            Placar
          </label>
          <Input
            id={`placar-time-${team}`}
            type="number"
            min={0}
            inputMode="numeric"
            required={exigirPlacar}
            value={placar ?? ''}
            onChange={(e) =>
              onPlacarChange(e.target.value === '' ? null : Math.max(0, Number(e.target.value) || 0))
            }
            className="text-center"
          />
        </div>
      </div>

      {escalados.length === 0 ? (
        <p className="mt-4 rounded-control border border-dashed border-border px-4 py-6 text-center text-sm text-muted-foreground">
          Ninguém neste time ainda. Use a lista de disponíveis abaixo.
        </p>
      ) : (
        <ul className="mt-2">
          {escalados.map((escalado) => (
            <ParticipantRow
              key={escalado.player_id}
              escalado={escalado}
              mostrarEstatisticas={mostrarEstatisticas}
              onChange={(campo, valor) => onParticipanteChange(escalado.player_id, campo, valor)}
              onRemove={() => onRemover(escalado.player_id)}
            />
          ))}
        </ul>
      )}

      <p className="mt-3 text-sm text-muted-foreground">
        {escalados.length} {escalados.length === 1 ? 'jogador' : 'jogadores'}
        {mostrarEstatisticas && ` · ${somaDeGols} ${somaDeGols === 1 ? 'gol' : 'gols'} lançados`}
      </p>
    </section>
  )
}
