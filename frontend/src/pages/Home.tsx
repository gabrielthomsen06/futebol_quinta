import { CalendarPlus, Goal, Handshake } from 'lucide-react'
import { Suspense, lazy } from 'react'
import { Link } from 'react-router-dom'

import { EmptyState } from '@/components/common/EmptyState'
import { ErrorState } from '@/components/common/ErrorState'
import { PageHeader } from '@/components/common/PageHeader'
import { StatCard } from '@/components/common/StatCard'
import { ALTURA_DO_GRAFICO, ChartCard } from '@/components/charts/ChartCard'
import { LastMatchCard } from '@/components/dashboard/LastMatchCard'
import { NextMatchCard } from '@/components/dashboard/NextMatchCard'
import { TopPlayersList } from '@/components/dashboard/TopPlayersList'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { useAuth } from '@/hooks/useAuth'
import { useDashboard } from '@/hooks/useDashboard'

/**
 * O Recharts é pesado e esta é a primeira tela que abre no celular. Carregando
 * o gráfico sob demanda, o painel — que é o que importa — pinta primeiro.
 */
const GoalsOverTimeChart = lazy(() => import('@/components/charts/GoalsOverTimeChart'))

export function HomePage() {
  const { isAuthenticated } = useAuth()
  const { data, isPending, isError, error, refetch, isRefetching } = useDashboard()

  if (isPending) return <PainelCarregando />

  if (isError) {
    return (
      <ErrorState message={error.message} onRetry={() => void refetch()} retrying={isRefetching} />
    )
  }

  const { totals, next_match, last_match, top_scorers, top_assists, goals_timeline } = data
  const semNada = totals.matches_played === 0 && next_match === null && last_match === null

  return (
    <section>
      <PageHeader
        eyebrow={`Temporada ${data.season}`}
        title="Só no Migué FC"
        description="Futebol de segunda."
      />

      {semNada ? (
        <EmptyState
          icon={CalendarPlus}
          title="Nenhuma partida registrada"
          description="Assim que a primeira quinta-feira for registrada, os números aparecem aqui."
          action={
            isAuthenticated ? (
              <Button asChild>
                <Link to="/partidas/nova">Criar a primeira partida</Link>
              </Button>
            ) : undefined
          }
        />
      ) : (
        <div className="flex flex-col gap-4">
          <div className="grid grid-cols-3 gap-3">
            <StatCard value={totals.matches_played} label="Partidas" />
            <StatCard value={totals.goals_registered} label="Gols registrados" highlight />
            <StatCard value={totals.assists_registered} label="Assistências" />
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <NextMatchCard partida={next_match} />
            <LastMatchCard partida={last_match} />
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <TopPlayersList
              title="Artilharia"
              icon={Goal}
              entries={top_scorers}
              metric="goals"
              emptyMessage="Nenhum gol registrado na temporada"
            />
            <TopPlayersList
              title="Assistências"
              icon={Handshake}
              entries={top_assists}
              metric="assists"
              emptyMessage="Nenhuma assistência registrada na temporada"
            />
          </div>

          <ChartCard title="Evolução de gols" pontos={goals_timeline.length}>
            <Suspense fallback={<Skeleton className="h-full w-full" />}>
              <GoalsOverTimeChart pontos={goals_timeline} />
            </Suspense>
          </ChartCard>
        </div>
      )}
    </section>
  )
}

/** Esqueleto com a forma do painel, para a página não pular quando o dado chega. */
function PainelCarregando() {
  return (
    <section>
      <PageHeader eyebrow="Temporada" title="Só no Migué FC" description="Futebol de segunda." />
      <div className="flex flex-col gap-4">
        <div className="grid grid-cols-3 gap-3">
          {[0, 1, 2].map((i) => (
            <Skeleton key={i} className="h-28" />
          ))}
        </div>
        <div className="grid gap-4 lg:grid-cols-2">
          <Skeleton className="h-44" />
          <Skeleton className="h-44" />
        </div>
        <div className="grid gap-4 lg:grid-cols-2">
          <Skeleton className="h-72" />
          <Skeleton className="h-72" />
        </div>
        <Skeleton style={{ height: ALTURA_DO_GRAFICO + 80 }} />
      </div>
      <span role="status" className="sr-only">
        Carregando o painel...
      </span>
    </section>
  )
}

