import { CalendarPlus } from 'lucide-react'
import { Link } from 'react-router-dom'

import { EmptyState } from '@/components/common/EmptyState'
import { PageHeader } from '@/components/common/PageHeader'
// PROVISÓRIO (Fase 7): apagar esta importação e o arquivo na Fase 10.
import { ProvisionalMatchList } from '@/components/matches/ProvisionalMatchList'
import { Button } from '@/components/ui/button'
import { useAuth } from '@/hooks/useAuth'

/**
 * Histórico.
 *
 * A versão pública desta tela — cartões de partida, filtros de status e
 * período, "Ver detalhes" — é da Fase 10. Por ora, quem está autenticado vê
 * uma lista provisória que serve só para chegar ao formulário de edição.
 */
export function HistoryPage() {
  const { isAuthenticated } = useAuth()

  return (
    <section>
      <PageHeader
        eyebrow="Temporada 2026"
        title="Histórico"
        description="Todas as partidas da pelada."
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

      {isAuthenticated ? (
        <ProvisionalMatchList />
      ) : (
        <EmptyState
          icon={CalendarPlus}
          title="Em construção"
          description="A lista de partidas com filtros e detalhes chega na Fase 10."
        />
      )}
    </section>
  )
}
