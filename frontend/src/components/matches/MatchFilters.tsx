import { PeriodFilter } from '@/components/common/PeriodFilter'
import { cn } from '@/lib/utils'
import type { MatchStatus, PeriodSelection, Seasons } from '@/types/api'

const STATUS: { valor: MatchStatus | null; rotulo: string }[] = [
  { valor: null, rotulo: 'Todas' },
  { valor: 'SCHEDULED', rotulo: 'Agendadas' },
  { valor: 'PLAYED', rotulo: 'Realizadas' },
  { valor: 'CANCELLED', rotulo: 'Canceladas' },
]

interface MatchFiltersProps {
  status: MatchStatus | null
  onStatusChange: (status: MatchStatus | null) => void
  periodo: PeriodSelection
  onPeriodoChange: (periodo: PeriodSelection) => void
  seasons: Seasons | undefined
}

/** Status e período. O mesmo `PeriodFilter` que a tela de Rankings usa. */
export function MatchFilters({
  status,
  onStatusChange,
  periodo,
  onPeriodoChange,
  seasons,
}: MatchFiltersProps) {
  return (
    <div className="flex flex-col gap-4">
      <div role="group" aria-label="Filtrar por status" className="flex flex-wrap gap-2">
        {STATUS.map((opcao) => {
          const ativo = opcao.valor === status
          return (
            <button
              key={opcao.rotulo}
              type="button"
              aria-pressed={ativo}
              onClick={() => onStatusChange(opcao.valor)}
              className={cn(
                'min-h-11 rounded-control border px-4 text-label font-semibold uppercase transition-colors',
                ativo
                  ? 'border-primary bg-primary text-primary-foreground'
                  : 'border-border text-muted-foreground hover:text-foreground',
              )}
            >
              {opcao.rotulo}
            </button>
          )
        })}
      </div>

      <PeriodFilter value={periodo} onChange={onPeriodoChange} seasons={seasons} />
    </div>
  )
}
