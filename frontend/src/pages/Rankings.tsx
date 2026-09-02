import { CalendarPlus, Trophy } from 'lucide-react'
import { Suspense, lazy, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

import { EmptyState } from '@/components/common/EmptyState'
import { ErrorState } from '@/components/common/ErrorState'
import { LoadingState } from '@/components/common/LoadingState'
import { PageHeader } from '@/components/common/PageHeader'
import { ChartCard } from '@/components/charts/ChartCard'
import type { BarraDoGrafico } from '@/components/charts/PlayerBarChart'
import { MetricTabs, rotuloDaMetrica } from '@/components/rankings/MetricTabs'
import { PeriodFilter } from '@/components/rankings/PeriodFilter'
import { RankingList } from '@/components/rankings/RankingList'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { useAuth } from '@/hooks/useAuth'
import { useRanking, useSeasons } from '@/hooks/useRankings'
import type { PeriodSelection, Ranking, RankingMetric } from '@/types/api'

/** Mesmo chunk lazy do Recharts criado na Fase 8. */
const PlayerBarChart = lazy(() => import('@/components/charts/PlayerBarChart'))

const NO_GRAFICO = 10

/** Extrai do que a API devolveu o valor da métrica — sem recalcular nada. */
function valorDaMetrica(entrada: Ranking['entries'][number], metric: RankingMetric): number {
  const p = entrada.player
  const mapa: Record<RankingMetric, number> = {
    goals: p.goals,
    assists: p.assists,
    wins: p.wins,
    games: p.games,
    goals_per_game: p.goals_per_game,
    assists_per_game: p.assists_per_game,
  }
  return mapa[metric]
}

export function RankingsPage() {
  const { isAuthenticated } = useAuth()
  const seasons = useSeasons()
  const [metric, setMetric] = useState<RankingMetric>('goals')
  const [periodo, setPeriodo] = useState<PeriodSelection>({ mode: 'season' })

  // A temporada corrente só é conhecida depois de /api/seasons responder.
  const periodoEfetivo: PeriodSelection =
    periodo.mode === 'season' && periodo.season === undefined
      ? { mode: 'season', season: seasons.data?.current }
      : periodo

  const pronto = periodoEfetivo.mode !== 'season' || periodoEfetivo.season !== undefined
  const ranking = useRanking(metric, periodoEfetivo)

  const barras = useMemo<BarraDoGrafico[]>(() => {
    if (!ranking.data) return []
    return ranking.data.entries
      .slice(0, NO_GRAFICO)
      .map((e) => ({ nome: e.player.nickname, valor: valorDaMetrica(e, metric) }))
      .filter((b) => b.valor > 0)
  }, [ranking.data, metric])

  const exigePiso = ranking.data !== undefined && ranking.data.min_games > 0

  return (
    <section>
      <PageHeader
        eyebrow="Temporada"
        title="Rankings"
        description="Quem mais fez pela pelada, por métrica e por período."
      />

      <div className="mb-6 flex flex-col gap-4">
        <PeriodFilter value={periodoEfetivo} onChange={setPeriodo} seasons={seasons.data} />
        <MetricTabs value={metric} onChange={setMetric} />
      </div>

      {exigePiso && (
        <p className="mb-4 rounded-control border border-border bg-card px-4 py-3 text-sm text-muted-foreground">
          Só entram jogadores com no mínimo{' '}
          <strong className="text-foreground">{ranking.data?.min_games} partidas</strong>{' '}
          realizadas no período — sem esse piso, quem jogou uma vez e fez três gols
          lideraria a média para sempre.
        </p>
      )}

      {(ranking.isPending || !pronto) && <LoadingState variant="list" rows={6} />}

      {ranking.isError && (
        <ErrorState
          message={ranking.error.message}
          onRetry={() => void ranking.refetch()}
          retrying={ranking.isRefetching}
        />
      )}

      {ranking.data && ranking.data.entries.length === 0 && (
        <EmptyState
          icon={exigePiso ? Trophy : CalendarPlus}
          {...vazio(exigePiso, ranking.data.min_games, isAuthenticated)}
        />
      )}

      {ranking.data && ranking.data.entries.length > 0 && (
        <div className="flex flex-col gap-6">
          <RankingList entries={ranking.data.entries} metric={metric} />

          <ChartCard title={`${rotuloDaMetrica(metric)} — top ${NO_GRAFICO}`} pontos={barras.length}>
            <Suspense fallback={<Skeleton className="h-full w-full" />}>
              <PlayerBarChart dados={barras} rotulo={rotuloDaMetrica(metric)} />
            </Suspense>
          </ChartCard>
        </div>
      )}
    </section>
  )
}

/**
 * Vazio não é um só.
 *
 * Um ranking de média vazio tem causa diferente de um período sem partida — e
 * dizer qual é evita que a pessoa ache que o sistema quebrou.
 */
function vazio(exigePiso: boolean, minGames: number, isAdmin: boolean) {
  if (exigePiso) {
    return {
      title: 'Ninguém alcançou o mínimo ainda',
      description: `Este ranking só considera quem tem ${minGames} ou mais partidas realizadas no período escolhido.`,
    }
  }
  return {
    title: 'Nenhuma partida realizada neste período',
    description: 'Escolha outro recorte, ou registre a partida que faltou.',
    action: isAdmin ? (
      <Button asChild variant="outline">
        <Link to="/partidas/nova">Nova partida</Link>
      </Button>
    ) : undefined,
  }
}

