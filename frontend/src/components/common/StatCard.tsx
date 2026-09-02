import type { LucideIcon } from 'lucide-react'

import { cn } from '@/lib/utils'

interface StatCardProps {
  value: number | string
  label: string
  icon?: LucideIcon
  /** Realce discreto, para o card principal de um grupo. */
  highlight?: boolean
  className?: string
}

/**
 * Número grande em laranja sobre um rótulo em caixa alta.
 *
 * O valor usa tabular-nums: numa fileira de cards, os dígitos ficam alinhados
 * em vez de dançar conforme o número muda.
 */
export function StatCard({
  value,
  label,
  icon: Icon,
  highlight = false,
  className,
}: StatCardProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center gap-1 rounded-card border border-border bg-card px-4 py-5 text-center',
        highlight && 'border-primary/40',
        className,
      )}
    >
      {Icon && <Icon aria-hidden className="mb-1 h-5 w-5 text-primary" />}
      <span className="tabular font-display text-stat text-primary">{value}</span>
      <span className="text-label font-semibold uppercase text-muted-foreground">{label}</span>
    </div>
  )
}
