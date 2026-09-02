import type { LucideIcon } from 'lucide-react'
import type { ReactNode } from 'react'

interface EmptyStateProps {
  icon?: LucideIcon
  /** Frase específica da situação, nunca genérica. */
  title: string
  description?: string
  action?: ReactNode
}

/**
 * Nada para mostrar — e isso precisa ser dito.
 *
 * A frase vem sempre de fora: "Nenhuma partida registrada" e "Nenhuma partida
 * agendada" são situações diferentes e merecem textos diferentes. Um "sem
 * resultados" genérico não ajuda ninguém a saber o que fazer.
 */
export function EmptyState({ icon: Icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-card border border-dashed border-border px-6 py-14 text-center">
      {Icon && <Icon aria-hidden className="h-8 w-8 text-subtle-foreground" />}
      <p className="font-display text-xl uppercase tracking-wide">{title}</p>
      {description && (
        <p className="max-w-sm text-sm text-muted-foreground">{description}</p>
      )}
      {action && <div className="mt-2">{action}</div>}
    </div>
  )
}
