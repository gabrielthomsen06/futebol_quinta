import { cn } from '@/lib/utils'
import type { RankingMetric } from '@/types/api'

export const METRICAS: { valor: RankingMetric; rotulo: string; curto: string }[] = [
  { valor: 'goals', rotulo: 'Artilharia', curto: 'Gols' },
  { valor: 'assists', rotulo: 'Assistências', curto: 'Assist.' },
  { valor: 'wins', rotulo: 'Vitórias', curto: 'Vitórias' },
  { valor: 'games', rotulo: 'Jogos', curto: 'Jogos' },
  { valor: 'goals_per_game', rotulo: 'Média de gols', curto: 'Média G' },
  { valor: 'assists_per_game', rotulo: 'Média de assistências', curto: 'Média A' },
]

export function rotuloDaMetrica(metric: RankingMetric): string {
  return METRICAS.find((m) => m.valor === metric)?.rotulo ?? ''
}

interface MetricTabsProps {
  value: RankingMetric
  onChange: (metric: RankingMetric) => void
}

/**
 * As seis métricas em chips.
 *
 * Fileira rolável no celular: seis chips não cabem em 375px, e quebrar em duas
 * linhas empurraria a lista para baixo da dobra. `aria-pressed` comunica o
 * estado a quem usa leitor de tela.
 */
export function MetricTabs({ value, onChange }: MetricTabsProps) {
  return (
    <div
      role="group"
      aria-label="Escolher métrica do ranking"
      className="-mx-5 flex gap-2 overflow-x-auto px-5 pb-1 md:mx-0 md:flex-wrap md:px-0"
    >
      {METRICAS.map((metrica) => {
        const ativo = metrica.valor === value
        return (
          <button
            key={metrica.valor}
            type="button"
            aria-pressed={ativo}
            onClick={() => onChange(metrica.valor)}
            className={cn(
              'min-h-11 flex-none rounded-control border px-4 text-label font-semibold uppercase transition-colors',
              ativo
                ? 'border-primary bg-primary text-primary-foreground'
                : 'border-border text-muted-foreground hover:text-foreground',
            )}
          >
            {metrica.rotulo}
          </button>
        )
      })}
    </div>
  )
}
