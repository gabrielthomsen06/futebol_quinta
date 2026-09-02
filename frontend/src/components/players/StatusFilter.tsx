import { cn } from '@/lib/utils'
import type { PlayerStatusFilter } from '@/types/api'

const OPCOES: { valor: PlayerStatusFilter; rotulo: string }[] = [
  { valor: 'active', rotulo: 'Ativos' },
  { valor: 'inactive', rotulo: 'Inativos' },
  { valor: 'all', rotulo: 'Todos' },
]

interface StatusFilterProps {
  value: PlayerStatusFilter
  onChange: (value: PlayerStatusFilter) => void
}

/**
 * Filtro de status em três chips.
 *
 * Chips em vez de um select: são três opções, e no celular tocar num botão é
 * mais rápido que abrir uma lista. `aria-pressed` comunica o estado a quem
 * usa leitor de tela, já que a diferença visual é de cor e borda.
 */
export function StatusFilter({ value, onChange }: StatusFilterProps) {
  return (
    <div role="group" aria-label="Filtrar por status" className="flex gap-2">
      {OPCOES.map((opcao) => {
        const ativo = opcao.valor === value
        return (
          <button
            key={opcao.valor}
            type="button"
            aria-pressed={ativo}
            onClick={() => onChange(opcao.valor)}
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
  )
}
