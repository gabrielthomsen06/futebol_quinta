import { cva, type VariantProps } from 'class-variance-authority'

import { cn } from '@/lib/utils'

/**
 * Situação da partida.
 *
 * O texto aparece sempre: a cor reforça, mas nunca é o único sinal — quem não
 * distingue as cores lê AGENDADA, REALIZADA ou CANCELADA do mesmo jeito.
 */
const badgeVariants = cva(
  'inline-flex items-center rounded-control border px-2.5 py-1 font-display text-label font-bold uppercase',
  {
    variants: {
      status: {
        SCHEDULED: 'border-primary text-primary-hi',
        PLAYED: 'border-primary bg-primary text-primary-foreground',
        CANCELLED: 'border-border text-muted-foreground line-through',
      },
    },
    defaultVariants: { status: 'SCHEDULED' },
  },
)

const ROTULOS = {
  SCHEDULED: 'Agendada',
  PLAYED: 'Realizada',
  CANCELLED: 'Cancelada',
} as const

export interface StatusBadgeProps extends VariantProps<typeof badgeVariants> {
  status: keyof typeof ROTULOS
  className?: string
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  return <span className={cn(badgeVariants({ status }), className)}>{ROTULOS[status]}</span>
}
