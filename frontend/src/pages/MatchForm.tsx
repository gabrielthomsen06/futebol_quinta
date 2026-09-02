import { Users } from 'lucide-react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { EmptyState } from '@/components/common/EmptyState'
import { ErrorState } from '@/components/common/ErrorState'
import { LoadingState } from '@/components/common/LoadingState'
import { PageHeader } from '@/components/common/PageHeader'
import { MatchForm } from '@/components/matches/MatchForm'
import { Button } from '@/components/ui/button'
import { toast } from '@/components/ui/toaster'
import { useCreateMatch, useMatch, useUpdateMatch } from '@/hooks/useMatches'
import { usePlayers } from '@/hooks/usePlayers'
import type { MatchWrite } from '@/types/api'
import { useState } from 'react'

/** Serve às rotas /partidas/nova e /partidas/:id/editar. */
export function MatchFormPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const editando = Boolean(id)
  const [erro, setErro] = useState<string | null>(null)

  // Todos os jogadores: o formulário decide quem mostrar. Editar uma partida
  // antiga pode envolver alguém que hoje está inativo.
  const jogadores = usePlayers('all')
  const partida = useMatch(id ?? '', editando)
  const criar = useCreateMatch()
  const atualizar = useUpdateMatch()

  const carregando = jogadores.isPending || (editando && partida.isPending)
  const falhou = jogadores.isError || (editando && partida.isError)

  if (carregando) return <LoadingState variant="list" rows={4} />

  if (falhou) {
    const mensagem = jogadores.error?.message ?? partida.error?.message
    return (
      <ErrorState
        message={mensagem}
        onRetry={() => {
          void jogadores.refetch()
          if (editando) void partida.refetch()
        }}
      />
    )
  }

  if (!jogadores.data || jogadores.data.length === 0) {
    return (
      <section>
        <PageHeader eyebrow="Administração" title="Nova partida" />
        <EmptyState
          icon={Users}
          title="Cadastre jogadores antes"
          description="Uma partida precisa de gente nos dois times. Comece pelo cadastro."
          action={
            <Button asChild variant="outline">
              <Link to="/jogadores">Ir para Jogadores</Link>
            </Button>
          }
        />
      </section>
    )
  }

  async function salvar(dados: MatchWrite) {
    setErro(null)
    try {
      if (editando && id) {
        await atualizar.mutateAsync({ id, dados })
        toast.success('Partida salva')
      } else {
        const criada = await criar.mutateAsync(dados)
        toast.success('Partida criada')
        // Na Fase 10 este destino passa a ser a página de detalhes.
        navigate(`/partidas/${criada.id}/editar`, { replace: true })
      }
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : 'Não foi possível salvar a partida.')
    }
  }

  return (
    <section>
      <PageHeader
        eyebrow="Administração"
        title={editando ? 'Editar partida' : 'Nova partida'}
        description={
          editando
            ? 'Alterar a escalação ou o placar já muda as estatísticas de todo mundo que jogou.'
            : 'Monte os dois times manualmente e informe o resultado, se a partida já aconteceu.'
        }
      />

      <MatchForm
        partida={partida.data ?? null}
        jogadores={jogadores.data}
        onSubmit={salvar}
        onCancel={() => navigate('/historico')}
        pending={criar.isPending || atualizar.isPending}
        error={erro}
      />
    </section>
  )
}
