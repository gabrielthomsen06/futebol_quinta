import type { ReactNode } from 'react'

interface PageHeaderProps {
  /** Rótulo pequeno em laranja acima do título. */
  eyebrow?: string
  title: string
  description?: string
  /** Ação à direita no desktop, abaixo no celular. */
  action?: ReactNode
}

/** Abertura padrão de toda página, para nenhuma inventar a própria. */
export function PageHeader({ eyebrow, title, description, action }: PageHeaderProps) {
  return (
    <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div>
        {eyebrow && (
          <p className="text-label font-semibold uppercase tracking-[0.2em] text-primary">
            {eyebrow}
          </p>
        )}
        <h1 className="mt-2 font-display text-title uppercase tracking-wide md:text-4xl">
          {title}
        </h1>
        {description && <p className="mt-2 max-w-prose text-muted-foreground">{description}</p>}
      </div>
      {action}
    </div>
  )
}
