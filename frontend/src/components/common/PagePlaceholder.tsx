import { Construction } from 'lucide-react'

import { EmptyState } from '@/components/common/EmptyState'
import { PageHeader } from '@/components/common/PageHeader'

interface PagePlaceholderProps {
  title: string
  /** Em qual fase esta tela ganha conteúdo de verdade. */
  phase: string
  description: string
}

/**
 * Marcador temporário das telas que só existem para provar o roteamento.
 *
 * Usa o PageHeader e o EmptyState de verdade: assim as telas provisórias já
 * mostram o design final, em vez de um visual paralelo que ninguém revisa.
 */
export function PagePlaceholder({ title, phase, description }: PagePlaceholderProps) {
  return (
    <section>
      <PageHeader eyebrow={phase} title={title} description={description} />
      <EmptyState
        icon={Construction}
        title="Ainda não implementada"
        description="A Fase 5 entrega o design system. Esta tela ganha conteúdo na fase indicada acima."
      />
    </section>
  )
}
