import type { ReactNode } from 'react'

/** Altura fixa: evita o pulo da página quando o gráfico termina de carregar. */
export const ALTURA_DO_GRAFICO = 260

interface ChartCardProps {
  title: string
  /** Quantos pontos existem. Abaixo de 2 não se desenha linha. */
  pontos: number
  children: ReactNode
}

/**
 * Moldura de gráfico.
 *
 * Com menos de dois pontos não há o que desenhar — uma linha de um ponto só é
 * um ponto solto, e passa a impressão de gráfico quebrado.
 */
export function ChartCard({ title, pontos, children }: ChartCardProps) {
  return (
    <section className="rounded-card border border-border bg-card p-5">
      <h2 className="font-display text-section uppercase text-gold">{title}</h2>

      <div className="mt-4" style={{ height: ALTURA_DO_GRAFICO }}>
        {pontos < 2 ? (
          <p className="flex h-full items-center justify-center text-center text-muted-foreground">
            Poucos dados para o gráfico ainda. Registre mais partidas.
          </p>
        ) : (
          children
        )}
      </div>
    </section>
  )
}
