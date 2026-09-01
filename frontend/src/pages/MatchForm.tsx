import { useParams } from 'react-router-dom'

import { PagePlaceholder } from '@/components/common/PagePlaceholder'

/** Serve às rotas /partidas/nova e /partidas/:id/editar. */
export function MatchFormPage() {
  const { id } = useParams<{ id: string }>()

  return (
    <PagePlaceholder
      title={id ? 'Editar partida' : 'Nova partida'}
      phase="Fase 7"
      description="Data, status, nomes dos times, seleção de jogadores, montagem manual dos times, placar e estatísticas individuais."
    />
  )
}
