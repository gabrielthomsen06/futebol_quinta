import { PageHeader } from '@/components/common/PageHeader'
import { Button } from '@/components/ui/button'
import { useHealth } from '@/hooks/useHealth'

/**
 * Placeholder da tela inicial.
 *
 * O indicador abaixo é técnico e proposital: prova que o frontend conversa com
 * o backend através do proxy, exercitando o TanStack Query nos três estados.
 * O dashboard de verdade — totais, próxima partida, última partida, rankings e
 * gráficos — chega na Fase 8 e substitui este bloco.
 */
export function HomePage() {
  const { data, isPending, isError, error, refetch, isRefetching } = useHealth()

  return (
    <section>
      <PageHeader
        eyebrow="Temporada 2026"
        title="Só no Migué FC"
        description="Futebol de segunda. O dashboard completo chega na Fase 8."
      />

      <div className="rounded-card border border-border bg-card p-5">
        <h2 className="font-display text-section uppercase text-muted-foreground">
          Verificação de infraestrutura
        </h2>

        {isPending && (
          <p className="mt-3 flex items-center gap-2 text-muted-foreground">
            <span aria-hidden className="h-2.5 w-2.5 animate-pulse rounded-full bg-muted-foreground" />
            Consultando o backend...
          </p>
        )}

        {isError && (
          <div className="mt-3">
            <p className="flex items-center gap-2 font-medium">
              <span aria-hidden className="h-2.5 w-2.5 rounded-full bg-destructive" />
              Backend: desconectado
            </p>
            <p className="mt-1 text-sm text-muted-foreground">{error.message}</p>
            <Button
              variant="outline"
              size="sm"
              onClick={() => void refetch()}
              disabled={isRefetching}
              className="mt-4"
            >
              {isRefetching ? 'Tentando...' : 'Tentar de novo'}
            </Button>
          </div>
        )}

        {data && (
          <dl className="mt-3 space-y-2 text-sm">
            <div className="flex items-center gap-2">
              <span aria-hidden className="h-2.5 w-2.5 rounded-full bg-primary" />
              <dt className="sr-only">Estado da API</dt>
              <dd className="font-medium">Backend: conectado</dd>
            </div>
            <div className="flex justify-between border-t border-border pt-2">
              <dt className="text-muted-foreground">Banco de dados</dt>
              <dd className="font-medium">{data.database === 'ok' ? 'acessível' : 'com erro'}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted-foreground">Versão da API</dt>
              <dd className="tabular font-medium">{data.version}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted-foreground">Temporada</dt>
              <dd className="tabular font-medium">{data.season}</dd>
            </div>
          </dl>
        )}
      </div>
    </section>
  )
}
