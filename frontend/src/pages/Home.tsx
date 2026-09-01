import { useHealth } from '@/hooks/useHealth'

/**
 * Placeholder da tela inicial.
 *
 * O indicador abaixo é técnico e proposital: é a prova de que o frontend
 * conversa com o backend através do proxy, exercitando o TanStack Query nos
 * três estados (carregando, erro e sucesso). O dashboard de verdade — totais,
 * próxima partida, última partida, rankings e gráficos — chega na Fase 8 e
 * substitui este bloco.
 */
export function HomePage() {
  const { data, isPending, isError, error, refetch, isRefetching } = useHealth()

  return (
    <section className="py-6">
      <p className="text-label font-semibold uppercase tracking-[0.2em] text-accent">
        Temporada 2026
      </p>
      <h1 className="mt-2 font-display text-4xl font-extrabold uppercase tracking-wide md:text-5xl">
        Só no Migué FC
      </h1>
      <p className="mt-1 font-display text-lg uppercase tracking-[0.18em] text-muted">
        Futebol de segunda
      </p>

      <div className="mt-8 rounded-card border border-line bg-card p-5">
        <h2 className="text-label font-semibold uppercase tracking-[0.15em] text-muted">
          Verificação de infraestrutura
        </h2>

        {isPending && (
          <p className="mt-3 flex items-center gap-2 text-muted">
            <span aria-hidden className="h-2.5 w-2.5 animate-pulse rounded-full bg-muted" />
            Consultando o backend...
          </p>
        )}

        {isError && (
          <div className="mt-3">
            <p className="flex items-center gap-2 font-medium text-fg">
              <span aria-hidden className="h-2.5 w-2.5 rounded-full bg-red-500" />
              Backend: desconectado
            </p>
            <p className="mt-1 text-sm text-muted">{error.message}</p>
            <button
              type="button"
              onClick={() => void refetch()}
              disabled={isRefetching}
              className="mt-4 min-h-11 rounded-control border border-accent px-4 text-label font-semibold uppercase tracking-widest text-accent-hi transition-colors hover:bg-accent hover:text-ink disabled:opacity-60"
            >
              {isRefetching ? 'Tentando...' : 'Tentar de novo'}
            </button>
          </div>
        )}

        {data && (
          <dl className="mt-3 space-y-2 text-sm">
            <div className="flex items-center gap-2">
              <span aria-hidden className="h-2.5 w-2.5 rounded-full bg-accent" />
              <dt className="sr-only">Estado da API</dt>
              <dd className="font-medium text-fg">Backend: conectado</dd>
            </div>
            <div className="flex justify-between border-t border-line pt-2">
              <dt className="text-muted">Banco de dados</dt>
              <dd className="font-medium">{data.database === 'ok' ? 'acessível' : 'com erro'}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted">Versão da API</dt>
              <dd className="tabular font-medium">{data.version}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted">Temporada</dt>
              <dd className="tabular font-medium">{data.season}</dd>
            </div>
          </dl>
        )}
      </div>

      <p className="mt-4 text-sm text-dim">
        Fase 2 — infraestrutura. O dashboard completo chega na Fase 8.
      </p>
    </section>
  )
}
