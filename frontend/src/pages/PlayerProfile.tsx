import { CalendarOff } from 'lucide-react'
import { Link, useParams } from 'react-router-dom'

import { EmptyState } from '@/components/common/EmptyState'
import { ErrorState } from '@/components/common/ErrorState'
import { LoadingState } from '@/components/common/LoadingState'
import { PlayerAvatar } from '@/components/common/PlayerAvatar'
import { PhotoField } from '@/components/players/PhotoField'
import { toast } from '@/components/ui/toaster'
import { useAuth } from '@/hooks/useAuth'
import { useDeletePhoto, usePlayerStats, useUploadPhoto } from '@/hooks/usePlayers'
import { formatarData, formatarMedia, formatarPercentual } from '@/lib/format'
import { cn } from '@/lib/utils'
import type { PlayerMatch } from '@/types/api'

const RESULTADO = {
  V: { rotulo: 'Vitória', classe: 'text-primary-hi' },
  E: { rotulo: 'Empate', classe: 'text-muted-foreground' },
  D: { rotulo: 'Derrota', classe: 'text-subtle-foreground' },
} as const

export function PlayerProfilePage() {
  const { id = '' } = useParams<{ id: string }>()
  const { isAuthenticated } = useAuth()
  const { data, isPending, isError, error, refetch, isRefetching } = usePlayerStats(id)
  const enviarFoto = useUploadPhoto()
  const removerFoto = useDeletePhoto()

  if (isPending) return <LoadingState variant="stats" />
  if (isError) {
    return (
      <ErrorState message={error.message} onRetry={() => void refetch()} retrying={isRefetching} />
    )
  }

  const { stats, history } = data
  const processandoFoto = enviarFoto.isPending || removerFoto.isPending

  async function trocarFoto(arquivo: File) {
    try {
      await enviarFoto.mutateAsync({ id, arquivo })
      toast.success('Foto atualizada')
    } catch (falha) {
      toast.error(falha instanceof Error ? falha.message : 'Não foi possível enviar a foto.')
    }
  }

  async function apagarFoto() {
    try {
      await removerFoto.mutateAsync(id)
      toast.success('Foto removida')
    } catch (falha) {
      toast.error(falha instanceof Error ? falha.message : 'Não foi possível remover a foto.')
    }
  }

  return (
    <section>
      <header className="flex flex-col items-center gap-4 pb-8 text-center sm:flex-row sm:items-end sm:text-left">
        <PlayerAvatar nickname={stats.nickname} photoPath={stats.photo_path} size="lg" />
        <div className="flex-1">
          <h1 className="font-display text-4xl font-extrabold uppercase tracking-wide">
            {stats.nickname}
          </h1>
          {stats.status === 'INACTIVE' && (
            <p className="mt-1 text-label font-semibold uppercase text-muted-foreground">
              Inativo — fora das próximas escalações, com o histórico preservado
            </p>
          )}
          {isAuthenticated && (
            <div className="mt-4 flex justify-center sm:justify-start">
              <PhotoField
                player={stats}
                onUpload={trocarFoto}
                onRemove={apagarFoto}
                onReject={(mensagem) => toast.error(mensagem)}
                pending={processandoFoto}
              />
            </div>
          )}
        </div>
      </header>

      <dl className="grid grid-cols-3 gap-3 border-y border-border py-6 text-center">
        <Numero valor={stats.games} rotulo="Jogos" />
        <Numero valor={stats.goals} rotulo="Gols" />
        <Numero valor={stats.assists} rotulo="Assistências" />
      </dl>

      <dl className="grid grid-cols-3 gap-3 border-b border-border py-6 text-center">
        <Numero valor={stats.wins} rotulo="Vitórias" discreto />
        <Numero valor={stats.draws} rotulo="Empates" discreto />
        <Numero valor={stats.losses} rotulo="Derrotas" discreto />
      </dl>

      <dl className="grid grid-cols-2 gap-3 border-b border-border py-6 sm:grid-cols-4">
        <Derivado rotulo="Média de gols" valor={formatarMedia(stats.goals_per_game)} />
        <Derivado rotulo="Média de assistências" valor={formatarMedia(stats.assists_per_game)} />
        <Derivado rotulo="Aproveitamento" valor={formatarPercentual(stats.win_rate)} />
        <Derivado rotulo="Participações em gols" valor={String(stats.goal_participations)} />
      </dl>

      <h2 className="mb-4 mt-8 font-display text-section uppercase text-gold">Histórico</h2>

      {history.length === 0 ? (
        <EmptyState
          icon={CalendarOff}
          title="Nenhuma partida realizada"
          description={`${stats.nickname} ainda não participou de uma partida concluída. Agendadas e canceladas não entram nas estatísticas.`}
        />
      ) : (
        <ul className="flex flex-col gap-2">
          {history.map((partida) => (
            <LinhaDoHistorico key={partida.match_id} partida={partida} />
          ))}
        </ul>
      )}
    </section>
  )
}

function Numero({
  valor,
  rotulo,
  discreto = false,
}: {
  valor: number
  rotulo: string
  discreto?: boolean
}) {
  return (
    <div>
      <dd
        className={cn(
          'tabular font-display text-stat',
          discreto ? 'text-foreground' : 'text-primary',
        )}
      >
        {valor}
      </dd>
      <dt className="text-label font-semibold uppercase text-muted-foreground">{rotulo}</dt>
    </div>
  )
}

function Derivado({ rotulo, valor }: { rotulo: string; valor: string }) {
  return (
    <div className="rounded-card border border-border bg-card px-4 py-3">
      <dd className="tabular font-display text-2xl font-extrabold">{valor}</dd>
      <dt className="text-label font-semibold uppercase text-muted-foreground">{rotulo}</dt>
    </div>
  )
}

function LinhaDoHistorico({ partida }: { partida: PlayerMatch }) {
  const resultado = RESULTADO[partida.result]
  // O time do jogador aparece primeiro, para o placar ser lido do ponto de
  // vista dele em vez de sempre do time 1.
  const dele = partida.team === 1
  const meuNome = dele ? partida.team_1_name : partida.team_2_name
  const meuPlacar = dele ? partida.team_1_score : partida.team_2_score
  const outroNome = dele ? partida.team_2_name : partida.team_1_name
  const outroPlacar = dele ? partida.team_2_score : partida.team_1_score

  return (
    <li>
      <Link
        to={`/partidas/${partida.match_id}`}
        className="flex flex-col gap-2 rounded-card border border-border bg-card p-4 transition-colors hover:border-primary/40 sm:flex-row sm:items-center sm:justify-between"
      >
        <div className="flex items-center gap-3">
          <span
            aria-hidden
            className={cn('font-display text-2xl font-extrabold', resultado.classe)}
          >
            {partida.result}
          </span>
          <span className="sr-only">{resultado.rotulo} em</span>
          <div>
            <p className="tabular text-sm text-muted-foreground">
              {formatarData(partida.match_date)}
            </p>
            <p className="font-display text-lg uppercase tracking-wide">
              {meuNome} <span className="tabular text-primary">{meuPlacar}</span>
              <span className="mx-1 text-muted-foreground">x</span>
              <span className="tabular">{outroPlacar}</span> {outroNome}
            </p>
          </div>
        </div>
        <p className="tabular text-sm text-muted-foreground">
          {partida.goals} {partida.goals === 1 ? 'gol' : 'gols'} ·{' '}
          {partida.assists} {partida.assists === 1 ? 'assistência' : 'assistências'}
        </p>
      </Link>
    </li>
  )
}
