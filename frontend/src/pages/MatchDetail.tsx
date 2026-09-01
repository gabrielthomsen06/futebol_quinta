import { useParams } from 'react-router-dom'

import { PagePlaceholder } from '@/components/common/PagePlaceholder'

export function MatchDetailPage() {
  const { id } = useParams<{ id: string }>()

  return (
    <PagePlaceholder
      title="Detalhes da partida"
      phase="Fase 10"
      description={`Placar e as duas escalações com gols e assistências. Partida: ${id ?? '—'}.`}
    />
  )
}
