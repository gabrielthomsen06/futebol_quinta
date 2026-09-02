import { Info } from 'lucide-react'
import { useMemo, useState, type FormEvent } from 'react'

import { MATCH_STATUS_LABELS } from '@/components/common/StatusBadge'
import { PlayerPicker } from '@/components/matches/PlayerPicker'
import { TeamPanel } from '@/components/matches/TeamPanel'
import type { Escalado } from '@/components/matches/ParticipantRow'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'
import type { MatchDetail, MatchStatus, MatchWrite, PlayerWithStats } from '@/types/api'

const STATUS: MatchStatus[] = ['SCHEDULED', 'PLAYED', 'CANCELLED']

interface MatchFormProps {
  /** Nulo cria; preenchido edita. */
  partida: MatchDetail | null
  jogadores: PlayerWithStats[]
  onSubmit: (dados: MatchWrite) => Promise<void>
  onCancel: () => void
  pending: boolean
  /** Mensagem de erro vinda da API. */
  error: string | null
}

function hoje(): string {
  const agora = new Date()
  const mes = String(agora.getMonth() + 1).padStart(2, '0')
  const dia = String(agora.getDate()).padStart(2, '0')
  return `${agora.getFullYear()}-${mes}-${dia}`
}

function escaladosIniciais(partida: MatchDetail | null): Escalado[] {
  if (!partida) return []
  return [
    ...partida.team_1.map((p) => ({ ...p, team: 1 as const })),
    ...partida.team_2.map((p) => ({ ...p, team: 2 as const })),
  ]
}

export function MatchForm({
  partida,
  jogadores,
  onSubmit,
  onCancel,
  pending,
  error,
}: MatchFormProps) {
  const [data, setData] = useState(partida?.match_date ?? hoje())
  const [status, setStatus] = useState<MatchStatus>(partida?.status ?? 'SCHEDULED')
  const [nome1, setNome1] = useState(partida?.team_1_name ?? 'TIME 1')
  const [nome2, setNome2] = useState(partida?.team_2_name ?? 'TIME 2')
  const [placar1, setPlacar1] = useState<number | null>(partida?.team_1_score ?? null)
  const [placar2, setPlacar2] = useState<number | null>(partida?.team_2_score ?? null)
  const [escalados, setEscalados] = useState<Escalado[]>(() => escaladosIniciais(partida))
  const [incluirInativos, setIncluirInativos] = useState(false)

  const realizada = status === 'PLAYED'

  /**
   * Disponíveis: quem não está escalado. Inativos ficam de fora por padrão —
   * mas quem já está no time continua no time, mesmo inativo, porque editar
   * uma partida antiga não pode reescrever quem jogou.
   */
  const disponiveis = useMemo(() => {
    const escaladosIds = new Set(escalados.map((e) => e.player_id))
    return jogadores.filter(
      (j) =>
        !escaladosIds.has(j.id) && (incluirInativos || j.status === 'ACTIVE'),
    )
  }, [jogadores, escalados, incluirInativos])

  const time1 = escalados.filter((e) => e.team === 1)
  const time2 = escalados.filter((e) => e.team === 2)

  const golsLancados = escalados.reduce((total, e) => total + e.goals, 0)
  const somaDoPlacar = (placar1 ?? 0) + (placar2 ?? 0)
  const divergencia = realizada && placar1 !== null && placar2 !== null && golsLancados !== somaDoPlacar

  function escalar(player: PlayerWithStats, team: 1 | 2) {
    setEscalados((atual) => [
      ...atual,
      {
        player_id: player.id,
        nickname: player.nickname,
        photo_path: player.photo_path,
        team,
        goals: 0,
        assists: 0,
      },
    ])
  }

  function remover(playerId: string) {
    setEscalados((atual) => atual.filter((e) => e.player_id !== playerId))
  }

  function alterarParticipante(playerId: string, campo: 'goals' | 'assists', valor: number) {
    setEscalados((atual) =>
      atual.map((e) => (e.player_id === playerId ? { ...e, [campo]: valor } : e)),
    )
  }

  async function enviar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    await onSubmit({
      match_date: data,
      status,
      team_1_name: nome1.trim(),
      team_2_name: nome2.trim(),
      // Placar fica guardado mesmo em partida não realizada: quem cancelou e
      // voltou atrás não perde o que já tinha digitado.
      team_1_score: placar1,
      team_2_score: placar2,
      participants: escalados.map((e) => ({
        player_id: e.player_id,
        team: e.team,
        goals: e.goals,
        assists: e.assists,
      })),
    })
  }

  return (
    <form onSubmit={enviar} className="flex flex-col gap-6">
      {error && (
        <p
          role="alert"
          className="rounded-control border border-destructive px-4 py-3 text-sm text-destructive"
        >
          {error}
        </p>
      )}

      <div className="flex flex-col gap-4 rounded-card border border-border bg-card p-4 sm:flex-row sm:items-end">
        <div className="flex flex-col gap-1 sm:w-48">
          <label htmlFor="match_date" className="text-label font-semibold uppercase text-muted-foreground">
            Data
          </label>
          {/* Input nativo: abre o seletor do sistema no celular e evita três
              dependências só para escolher um dia. */}
          <Input
            id="match_date"
            type="date"
            required
            value={data}
            onChange={(e) => setData(e.target.value)}
          />
        </div>

        <fieldset className="flex flex-col gap-1">
          <legend className="mb-1 text-label font-semibold uppercase text-muted-foreground">
            Status
          </legend>
          <div className="flex gap-2">
            {STATUS.map((opcao) => (
              <button
                key={opcao}
                type="button"
                aria-pressed={status === opcao}
                onClick={() => setStatus(opcao)}
                className={cn(
                  'min-h-11 rounded-control border px-4 text-label font-semibold uppercase transition-colors',
                  status === opcao
                    ? 'border-primary bg-primary text-primary-foreground'
                    : 'border-border text-muted-foreground hover:text-foreground',
                )}
              >
                {MATCH_STATUS_LABELS[opcao]}
              </button>
            ))}
          </div>
        </fieldset>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <TeamPanel
          team={1}
          nome={nome1}
          onNomeChange={setNome1}
          placar={placar1}
          onPlacarChange={setPlacar1}
          escalados={time1}
          mostrarEstatisticas={realizada}
          exigirPlacar={realizada}
          onParticipanteChange={alterarParticipante}
          onRemover={remover}
        />
        <TeamPanel
          team={2}
          nome={nome2}
          onNomeChange={setNome2}
          placar={placar2}
          onPlacarChange={setPlacar2}
          escalados={time2}
          mostrarEstatisticas={realizada}
          exigirPlacar={realizada}
          onParticipanteChange={alterarParticipante}
          onRemover={remover}
        />
      </div>

      <PlayerPicker
        disponiveis={disponiveis}
        nomeTime1={nome1}
        nomeTime2={nome2}
        incluirInativos={incluirInativos}
        onIncluirInativos={setIncluirInativos}
        onEscalar={escalar}
      />

      {divergencia && (
        // Aviso, nunca bloqueio: o placar é o resultado oficial e os gols vêm
        // da folha anotada durante o jogo. Os dois podem não fechar.
        <p className="flex items-start gap-2 rounded-control border border-border bg-card px-4 py-3 text-sm text-muted-foreground">
          <Info aria-hidden className="mt-0.5 h-4 w-4 shrink-0 text-gold" />
          <span>
            Gols lançados: <strong className="tabular">{golsLancados}</strong> · placar:{' '}
            <strong className="tabular">{somaDoPlacar}</strong>. Isso é permitido — o
            placar é o resultado oficial e os gols individuais são anotados à parte.
          </span>
        </p>
      )}

      <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
        <Button type="button" variant="ghost" onClick={onCancel} disabled={pending}>
          Cancelar
        </Button>
        <Button type="submit" size="lg" disabled={pending}>
          {pending ? 'Salvando...' : 'Salvar partida'}
        </Button>
      </div>
    </form>
  )
}
