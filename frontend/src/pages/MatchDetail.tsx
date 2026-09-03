import { ArrowLeft, Ban, CalendarClock, Pencil, Trash2 } from 'lucide-react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { ConfirmDialog } from '@/components/common/ConfirmDialog'
import { EmptyState } from '@/components/common/EmptyState'
import { ErrorState } from '@/components/common/ErrorState'
import { LoadingState } from '@/components/common/LoadingState'
import { StatusBadge } from '@/components/common/StatusBadge'
import { MatchScore } from '@/components/matches/MatchScore'
import { TeamLineup } from '@/components/matches/TeamLineup'
import { Button } from '@/components/ui/button'
import { toast } from '@/components/ui/toaster'
import { ApiError } from '@/api/client'
import { useAuth } from '@/hooks/useAuth'
import { useDeleteMatch, useMatch } from '@/hooks/useMatches'
import { formatarData } from '@/lib/format'

export function MatchDetailPage() {
  const { id = '' } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { isAuthenticated } = useAuth()
  const { data, isPending, isError, error, refetch, isRefetching } = useMatch(id)
  const excluir = useDeleteMatch()

  if (isPending) return <LoadingState variant="stats" />

  if (isError) {
    // Link antigo de partida já excluída é o caso comum aqui — merece uma
    // tela própria, e não o erro genérico.
    if (error instanceof ApiError && error.status === 404) {
      return (
        <EmptyState
          icon={Ban}
          title="Partida não encontrada"
          description="Ela pode ter sido excluída, ou o endereço está errado."
          action={
            <Button asChild variant="outline">
              <Link to="/historico">Ver o histórico</Link>
            </Button>
          }
        />
      )
    }
    return (
      <ErrorState message={error.message} onRetry={() => void refetch()} retrying={isRefetching} />
    )
  }

  const realizada = data.status === 'PLAYED'
  const temPlacar = data.team_1_score !== null && data.team_2_score !== null
  const semEscalacao = data.team_1.length === 0 && data.team_2.length === 0

  async function remover() {
    try {
      await excluir.mutateAsync(id)
      toast.success('Partida excluída')
      navigate('/historico', { replace: true })
    } catch (falha) {
      toast.error(falha instanceof Error ? falha.message : 'Não foi possível excluir.')
    }
  }

  return (
    <section>
      <Link
        to="/historico"
        className="mb-4 inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft aria-hidden className="h-4 w-4" />
        Histórico
      </Link>

      <header className="rounded-card border border-border bg-card p-6">
        <div className="flex items-center justify-between gap-3">
          <span className="tabular text-sm text-muted-foreground">
            {formatarData(data.match_date)}
          </span>
          <StatusBadge status={data.status} />
        </div>

        <div className="mt-6 flex items-center justify-center gap-4 text-center">
          <span className="flex-1 font-display text-xl uppercase tracking-wide md:text-2xl">
            {data.team_1_name}
          </span>
          {realizada && temPlacar ? (
            <MatchScore home={data.team_1_score!} away={data.team_2_score!} size="lg" />
          ) : (
            <span aria-hidden className="font-display text-stat text-muted-foreground">
              x
            </span>
          )}
          <span className="flex-1 font-display text-xl uppercase tracking-wide md:text-2xl">
            {data.team_2_name}
          </span>
        </div>

        {data.status === 'SCHEDULED' && (
          <p className="mt-5 flex items-center justify-center gap-2 text-sm text-muted-foreground">
            <CalendarClock aria-hidden className="h-4 w-4" />
            Partida ainda não realizada. Não entra nas estatísticas.
          </p>
        )}

        {data.status === 'CANCELLED' && (
          <p className="mt-5 flex items-center justify-center gap-2 text-sm text-muted-foreground">
            <Ban aria-hidden className="h-4 w-4 text-destructive" />
            Partida cancelada. Não entra em nenhuma estatística.
          </p>
        )}
      </header>

      {semEscalacao ? (
        <div className="mt-4">
          <EmptyState
            icon={CalendarClock}
            title="Times ainda não definidos"
            description="A escalação aparece aqui assim que os times forem montados."
          />
        </div>
      ) : (
        <div className="mt-4 grid gap-4 lg:grid-cols-2">
          <TeamLineup
            nome={data.team_1_name}
            placar={realizada ? data.team_1_score : null}
            jogadores={data.team_1}
            mostrarEstatisticas={realizada}
            vencedor={realizada && temPlacar && data.team_1_score! > data.team_2_score!}
          />
          <TeamLineup
            nome={data.team_2_name}
            placar={realizada ? data.team_2_score : null}
            jogadores={data.team_2}
            mostrarEstatisticas={realizada}
            vencedor={realizada && temPlacar && data.team_2_score! > data.team_1_score!}
          />
        </div>
      )}

      {isAuthenticated && (
        <div className="mt-6 flex flex-wrap justify-end gap-2">
          <Button asChild variant="outline">
            <Link to={`/partidas/${id}/editar`}>
              <Pencil aria-hidden />
              Editar
            </Link>
          </Button>
          <ConfirmDialog
            trigger={
              <Button variant="destructive" disabled={excluir.isPending}>
                <Trash2 aria-hidden />
                Excluir
              </Button>
            }
            title="Excluir a partida?"
            description={`${formatarData(data.match_date)} — ${data.team_1_name} ${
              data.team_1_score ?? '-'
            } x ${data.team_2_score ?? '-'} ${data.team_2_name}, com ${
              data.team_1.length + data.team_2.length
            } jogadores. As estatísticas dela somem dos rankings e dos perfis. Não dá para desfazer.`}
            onConfirm={remover}
            loading={excluir.isPending}
          />
        </div>
      )}
    </section>
  )
}
