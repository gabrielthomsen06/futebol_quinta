import { CalendarPlus } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'

import { EmptyState } from '@/components/common/EmptyState'
import { ErrorState } from '@/components/common/ErrorState'
import { LoadingState } from '@/components/common/LoadingState'
import { PageHeader } from '@/components/common/PageHeader'
import { MatchCard } from '@/components/matches/MatchCard'
import { MatchFilters } from '@/components/matches/MatchFilters'
import { Button } from '@/components/ui/button'
import { useAuth } from '@/hooks/useAuth'
import { useMatchHistory } from '@/hooks/useMatches'
import { useSeasons } from '@/hooks/useRankings'
import type { MatchStatus, PeriodSelection } from '@/types/api'

export function HistoryPage() {
  const { isAuthenticated } = useAuth()
  const seasons = useSeasons()
  const [status, setStatus] = useState<MatchStatus | null>(null)
  const [periodo, setPeriodo] = useState<PeriodSelection>({ mode: 'all' })

  const historico = useMatchHistory({ status, periodo })

  const partidas = historico.data?.pages.flatMap((p) => p.items) ?? []
  const total = historico.data?.pages[0]?.total ?? 0

  return (
    <section>
      <PageHeader
        eyebrow="Temporada 2026"
        title="Histórico"
        description="Todas as partidas da pelada, da mais recente para a mais antiga."
        action={
          isAuthenticated ? (
            <Button asChild>
              <Link to="/partidas/nova">
                <CalendarPlus aria-hidden />
                Nova partida
              </Link>
            </Button>
          ) : undefined
        }
      />

      <div className="mb-6">
        <MatchFilters
          status={status}
          onStatusChange={setStatus}
          periodo={periodo}
          onPeriodoChange={setPeriodo}
          seasons={seasons.data}
        />
      </div>

      {historico.isPending && <LoadingState variant="list" rows={4} />}

      {historico.isError && (
        <ErrorState
          message={historico.error.message}
          onRetry={() => void historico.refetch()}
          retrying={historico.isRefetching}
        />
      )}

      {historico.data && partidas.length === 0 && (
        <EmptyState
          icon={CalendarPlus}
          {...vazio(status !== null || periodo.mode !== 'all', isAuthenticated)}
        />
      )}

      {partidas.length > 0 && (
        <>
          <p className="mb-3 text-sm text-muted-foreground">
            {partidas.length} de {total} {total === 1 ? 'partida' : 'partidas'}
          </p>

          <ul className="flex flex-col gap-3">
            {partidas.map((partida) => (
              <MatchCard key={partida.id} partida={partida} />
            ))}
          </ul>

          {historico.hasNextPage && (
            <div className="mt-6 flex justify-center">
              <Button
                variant="outline"
                onClick={() => void historico.fetchNextPage()}
                disabled={historico.isFetchingNextPage}
              >
                {historico.isFetchingNextPage ? 'Carregando...' : 'Carregar mais partidas'}
              </Button>
            </div>
          )}
        </>
      )}
    </section>
  )
}

/** Filtro sem resultado é diferente de banco sem partida. */
function vazio(temFiltro: boolean, isAdmin: boolean) {
  if (temFiltro) {
    return {
      title: 'Nenhuma partida com esse filtro',
      description: 'Tente outro status ou outro recorte de período.',
    }
  }
  return {
    title: 'Nenhuma partida registrada',
    description: 'Registre a primeira quinta-feira para o histórico começar.',
    action: isAdmin ? (
      <Button asChild variant="outline">
        <Link to="/partidas/nova">Nova partida</Link>
      </Button>
    ) : undefined,
  }
}
