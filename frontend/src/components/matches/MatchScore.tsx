import { cn } from '@/lib/utils'

const TAMANHOS = {
  sm: 'text-2xl',
  md: 'text-stat',
  lg: 'text-stat-xl',
} as const

interface MatchScoreProps {
  home: number
  away: number
  size?: keyof typeof TAMANHOS
  className?: string
}

/**
 * O placar, e só isso.
 *
 * Apresentação pura: recebe dois números e destaca o maior. **Não sabe o que é
 * status**, não decide se deve aparecer e não consulta regra nenhuma — quem
 * sabe que partida agendada não tem placar é a tela que o chama.
 *
 * É o que permite o mesmo componente servir ao card do histórico, à página de
 * detalhes e ao card do dashboard sem acumular condicionais.
 */
export function MatchScore({ home, away, size = 'md', className }: MatchScoreProps) {
  return (
    <span className={cn('tabular font-display font-extrabold', TAMANHOS[size], className)}>
      <span className={home > away ? 'text-primary' : 'text-foreground'}>{home}</span>
      <span className="mx-2 text-muted-foreground">x</span>
      <span className={away > home ? 'text-primary' : 'text-foreground'}>{away}</span>
    </span>
  )
}
