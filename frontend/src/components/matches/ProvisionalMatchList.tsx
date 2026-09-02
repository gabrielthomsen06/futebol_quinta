/**
 * ============================================================================
 * PROVISÓRIO — DESCARTÁVEL NA FASE 10
 * ============================================================================
 *
 * Esta lista existe por um motivo só: sem ela, a Fase 7 entrega o formulário de
 * partida sem nenhum caminho para chegar até uma partida já criada — só daria
 * para editar quem soubesse o UUID e digitasse a URL.
 *
 * Ela é deliberadamente pobre: sem filtro, sem card, sem paginação, sem link
 * para detalhes, e só aparece para administrador autenticado.
 *
 * **Na Fase 10:** apague este arquivo e a importação em `pages/History.tsx`.
 * O Histórico definitivo é público, com filtros de status e período, cartões de
 * partida e "Ver detalhes". Nada aqui deve ser aproveitado.
 * ============================================================================
 */

import { CalendarPlus, Pencil, Trash2 } from 'lucide-react'
import { Link } from 'react-router-dom'

import { ConfirmDialog } from '@/components/common/ConfirmDialog'
import { EmptyState } from '@/components/common/EmptyState'
import { ErrorState } from '@/components/common/ErrorState'
import { LoadingState } from '@/components/common/LoadingState'
import { StatusBadge } from '@/components/common/StatusBadge'
import { Button } from '@/components/ui/button'
import { toast } from '@/components/ui/toaster'
import { useDeleteMatch, useMatches } from '@/hooks/useMatches'
import { formatarData } from '@/lib/format'
import type { Match } from '@/types/api'

export function ProvisionalMatchList() {
  const { data, isPending, isError, error, refetch, isRefetching } = useMatches()
  const excluir = useDeleteMatch()

  if (isPending) return <LoadingState variant="list" rows={4} />
  if (isError) {
    return (
      <ErrorState message={error.message} onRetry={() => void refetch()} retrying={isRefetching} />
    )
  }

  async function remover(partida: Match) {
    try {
      await excluir.mutateAsync(partida.id)
      toast.success('Partida excluída')
    } catch (falha) {
      toast.error(falha instanceof Error ? falha.message : 'Não foi possível excluir.')
    }
  }

  if (data.items.length === 0) {
    return (
      <EmptyState
        icon={CalendarPlus}
        title="Nenhuma partida registrada"
        description="Registre a primeira quinta-feira para as estatísticas começarem a existir."
        action={
          <Button asChild>
            <Link to="/partidas/nova">Nova partida</Link>
          </Button>
        }
      />
    )
  }

  return (
    <ul className="flex flex-col gap-2">
      {data.items.map((partida) => (
        <li
          key={partida.id}
          className="flex flex-wrap items-center gap-3 rounded-card border border-border bg-card p-4"
        >
          <span className="tabular text-sm text-muted-foreground">
            {formatarData(partida.match_date)}
          </span>

          <span className="min-w-0 flex-1 font-display text-lg uppercase tracking-wide">
            {partida.team_1_name}{' '}
            {partida.status === 'PLAYED' && (
              <>
                <span className="tabular text-primary">{partida.team_1_score}</span>
                <span className="mx-1 text-muted-foreground">x</span>
                <span className="tabular text-primary">{partida.team_2_score}</span>{' '}
              </>
            )}
            {partida.status !== 'PLAYED' && <span className="mx-1 text-muted-foreground">x</span>}
            {partida.team_2_name}
          </span>

          <StatusBadge status={partida.status} />

          <div className="flex gap-2">
            <Button asChild variant="ghost" size="sm">
              <Link to={`/partidas/${partida.id}/editar`}>
                <Pencil aria-hidden />
                Editar
              </Link>
            </Button>
            <ConfirmDialog
              trigger={
                <Button variant="ghost" size="sm" disabled={excluir.isPending}>
                  <Trash2 aria-hidden />
                  Excluir
                </Button>
              }
              title="Excluir a partida?"
              description={`${formatarData(partida.match_date)} — ${partida.team_1_name} ${
                partida.team_1_score ?? '-'
              } x ${partida.team_2_score ?? '-'} ${partida.team_2_name}. As estatísticas dela somem dos rankings e dos perfis. Não dá para desfazer.`}
              onConfirm={() => remover(partida)}
              loading={excluir.isPending}
            />
          </div>
        </li>
      ))}
    </ul>
  )
}
