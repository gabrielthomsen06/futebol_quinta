import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'
import type { PeriodMode, PeriodSelection, Seasons } from '@/types/api'

const MODOS: { valor: PeriodMode; rotulo: string }[] = [
  { valor: 'season', rotulo: 'Temporada' },
  { valor: 'month', rotulo: 'Mês' },
  { valor: 'range', rotulo: 'Período' },
  { valor: 'all', rotulo: 'Geral' },
]

interface PeriodFilterProps {
  value: PeriodSelection
  onChange: (periodo: PeriodSelection) => void
  seasons: Seasons | undefined
}

/**
 * Recorte de período em quatro modos.
 *
 * Controles nativos de propósito: `<select>`, `<input type="month">` e
 * `<input type="date">` abrem o seletor do sistema no celular e não custam
 * nenhuma dependência. "Geral" não tem controle — é a ausência de filtro.
 */
export function PeriodFilter({ value, onChange, seasons }: PeriodFilterProps) {
  const anos = seasons?.available.length ? seasons.available : [seasons?.current ?? 2026]

  function trocarModo(mode: PeriodMode) {
    if (mode === value.mode) return
    // Cada modo começa limpo, com um padrão sensato: nunca se envia ao
    // servidor resto de um recorte anterior.
    onChange(
      mode === 'season'
        ? { mode, season: value.season ?? seasons?.current ?? anos[0] }
        : { mode },
    )
  }

  return (
    <div className="flex flex-col gap-3">
      <div role="group" aria-label="Recorte de período" className="flex flex-wrap gap-2">
        {MODOS.map((modo) => {
          const ativo = modo.valor === value.mode
          return (
            <button
              key={modo.valor}
              type="button"
              aria-pressed={ativo}
              onClick={() => trocarModo(modo.valor)}
              className={cn(
                'min-h-11 rounded-control border px-4 text-label font-semibold uppercase transition-colors',
                ativo
                  ? 'border-primary text-primary-hi'
                  : 'border-border text-muted-foreground hover:text-foreground',
              )}
            >
              {modo.rotulo}
            </button>
          )
        })}
      </div>

      {value.mode === 'season' && (
        <div className="flex flex-col gap-1">
          <label htmlFor="temporada" className="text-label font-semibold uppercase text-muted-foreground">
            Temporada
          </label>
          <select
            id="temporada"
            value={value.season ?? anos[0]}
            onChange={(e) => onChange({ mode: 'season', season: Number(e.target.value) })}
            className="min-h-12 w-full rounded-control border border-input bg-card px-4 text-foreground sm:w-48"
          >
            {anos.map((ano) => (
              <option key={ano} value={ano}>
                {ano}
              </option>
            ))}
          </select>
        </div>
      )}

      {value.mode === 'month' && (
        <div className="flex flex-col gap-1">
          <label htmlFor="mes" className="text-label font-semibold uppercase text-muted-foreground">
            Mês
          </label>
          <Input
            id="mes"
            type="month"
            value={value.month ?? ''}
            onChange={(e) => onChange({ mode: 'month', month: e.target.value })}
            className="sm:w-48"
          />
        </div>
      )}

      {value.mode === 'range' && (
        <div className="flex flex-wrap gap-3">
          <div className="flex flex-col gap-1">
            <label htmlFor="de" className="text-label font-semibold uppercase text-muted-foreground">
              De
            </label>
            <Input
              id="de"
              type="date"
              value={value.dateFrom ?? ''}
              onChange={(e) => onChange({ ...value, mode: 'range', dateFrom: e.target.value })}
              className="sm:w-44"
            />
          </div>
          <div className="flex flex-col gap-1">
            <label htmlFor="ate" className="text-label font-semibold uppercase text-muted-foreground">
              Até
            </label>
            <Input
              id="ate"
              type="date"
              value={value.dateTo ?? ''}
              onChange={(e) => onChange({ ...value, mode: 'range', dateTo: e.target.value })}
              className="sm:w-44"
            />
          </div>
        </div>
      )}
    </div>
  )
}
