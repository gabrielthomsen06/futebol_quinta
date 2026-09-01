import { useParams } from 'react-router-dom'

import { PagePlaceholder } from '@/components/common/PagePlaceholder'

export function PlayerProfilePage() {
  const { id } = useParams<{ id: string }>()

  return (
    <PagePlaceholder
      title="Perfil do jogador"
      phase="Fase 6"
      description={`Foto grande, agregados, médias, aproveitamento e histórico individual. Jogador: ${id ?? '—'}.`}
    />
  )
}
