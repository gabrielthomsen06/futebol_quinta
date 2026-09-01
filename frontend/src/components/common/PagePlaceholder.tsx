interface PagePlaceholderProps {
  title: string
  /** Em qual fase esta tela ganha conteúdo de verdade. */
  phase: string
  description: string
}

/**
 * Marcador temporário das telas que só existem para provar o roteamento.
 * Cada uma é substituída pela implementação real na fase indicada.
 */
export function PagePlaceholder({ title, phase, description }: PagePlaceholderProps) {
  return (
    <section className="py-6">
      <p className="text-label font-semibold uppercase tracking-[0.2em] text-accent">{phase}</p>
      <h1 className="mt-2 font-display text-4xl font-extrabold uppercase tracking-wide">{title}</h1>
      <p className="mt-3 max-w-prose text-muted">{description}</p>
      <p className="mt-6 rounded-card border border-line bg-card px-4 py-3 text-sm text-dim">
        Tela ainda não implementada. A Fase 2 entrega apenas a infraestrutura.
      </p>
    </section>
  )
}
