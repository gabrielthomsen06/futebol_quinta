import { Search, UserPlus, Users } from 'lucide-react'
import { useMemo, useState } from 'react'

import { EmptyState } from '@/components/common/EmptyState'
import { ErrorState } from '@/components/common/ErrorState'
import { LoadingState } from '@/components/common/LoadingState'
import { PageHeader } from '@/components/common/PageHeader'
import { PlayerCard } from '@/components/players/PlayerCard'
import { PlayerFormDialog } from '@/components/players/PlayerFormDialog'
import { StatusFilter } from '@/components/players/StatusFilter'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { toast } from '@/components/ui/toaster'
import { useAuth } from '@/hooks/useAuth'
import { useCreatePlayer, usePlayers, useSetPlayerStatus, useUpdatePlayer } from '@/hooks/usePlayers'
import type { PlayerStatusFilter, PlayerWithStats } from '@/types/api'

export function PlayersPage() {
  const { isAuthenticated } = useAuth()
  const [status, setStatus] = useState<PlayerStatusFilter>('active')
  const [busca, setBusca] = useState('')
  const [dialogAberto, setDialogAberto] = useState(false)
  const [emEdicao, setEmEdicao] = useState<PlayerWithStats | null>(null)
  const [erroForm, setErroForm] = useState<string | null>(null)

  const { data, isPending, isError, error, refetch, isRefetching } = usePlayers(status)
  const criar = useCreatePlayer()
  const editar = useUpdatePlayer()
  const trocarStatus = useSetPlayerStatus()

  /**
   * A busca filtra no cliente de propósito: são pouco mais de uma dúzia de
   * jogadores, e disparar uma requisição por tecla digitada seria desperdício.
   */
  const jogadores = useMemo(() => {
    if (!data) return []
    const termo = busca.trim().toLowerCase()
    if (!termo) return data
    return data.filter((j) => j.nickname.toLowerCase().includes(termo))
  }, [data, busca])

  function abrirCriacao() {
    setEmEdicao(null)
    setErroForm(null)
    setDialogAberto(true)
  }

  function abrirEdicao(player: PlayerWithStats) {
    setEmEdicao(player)
    setErroForm(null)
    setDialogAberto(true)
  }

  async function salvar(nickname: string) {
    setErroForm(null)
    try {
      if (emEdicao) {
        await editar.mutateAsync({ id: emEdicao.id, nickname })
        toast.success('Jogador atualizado')
      } else {
        await criar.mutateAsync(nickname)
        toast.success('Jogador criado')
      }
      setDialogAberto(false)
    } catch (falha) {
      // Apelido repetido volta como 409 com mensagem pronta do servidor.
      setErroForm(falha instanceof Error ? falha.message : 'Não foi possível salvar.')
    }
  }

  async function alternarStatus(player: PlayerWithStats) {
    const novo = player.status === 'ACTIVE' ? 'INACTIVE' : 'ACTIVE'
    try {
      await trocarStatus.mutateAsync({ id: player.id, status: novo })
      toast.success(
        novo === 'INACTIVE'
          ? `${player.nickname} ficou inativo. O histórico dele continua.`
          : `${player.nickname} voltou para as escalações.`,
      )
    } catch (falha) {
      toast.error(falha instanceof Error ? falha.message : 'Não foi possível alterar.')
    }
  }

  return (
    <section>
      <PageHeader
        eyebrow="Temporada 2026"
        title="Jogadores"
        description="Quem joga a pelada de quinta."
        action={
          isAuthenticated ? (
            <Button onClick={abrirCriacao}>
              <UserPlus aria-hidden />
              Novo jogador
            </Button>
          ) : undefined
        }
      />

      <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="relative sm:max-w-xs">
          <Search
            aria-hidden
            className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-subtle-foreground"
          />
          <Input
            type="search"
            value={busca}
            onChange={(e) => setBusca(e.target.value)}
            placeholder="Buscar jogador..."
            aria-label="Buscar jogador pelo apelido"
            className="pl-11"
          />
        </div>
        <StatusFilter value={status} onChange={setStatus} />
      </div>

      {isPending && <LoadingState variant="cards" rows={6} />}

      {isError && (
        <ErrorState
          message={error.message}
          onRetry={() => void refetch()}
          retrying={isRefetching}
        />
      )}

      {data && jogadores.length === 0 && (
        <EmptyState
          icon={Users}
          {...vazio(busca, status, data.length, isAuthenticated, abrirCriacao)}
        />
      )}

      {jogadores.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {jogadores.map((player) => (
            <PlayerCard
              key={player.id}
              player={player}
              isAdmin={isAuthenticated}
              onEdit={abrirEdicao}
              onToggleStatus={alternarStatus}
              pending={trocarStatus.isPending}
            />
          ))}
        </div>
      )}

      <PlayerFormDialog
        open={dialogAberto}
        onOpenChange={setDialogAberto}
        player={emEdicao}
        onSubmit={salvar}
        pending={criar.isPending || editar.isPending}
        error={erroForm}
      />
    </section>
  )
}

/**
 * Vazio não é um só: "ninguém cadastrado", "a busca não achou" e "não há
 * inativos" são situações diferentes e pedem frases diferentes.
 */
function vazio(
  busca: string,
  status: PlayerStatusFilter,
  totalCarregado: number,
  isAdmin: boolean,
  onCriar: () => void,
) {
  if (busca.trim() && totalCarregado > 0) {
    return {
      title: 'Nenhum jogador com esse apelido',
      description: `Nada encontrado para "${busca.trim()}". Confira a escrita ou limpe a busca.`,
    }
  }
  if (status === 'inactive') {
    return {
      title: 'Nenhum jogador inativo',
      description: 'Todo mundo do grupo está ativo no momento.',
    }
  }
  return {
    title: 'Nenhum jogador cadastrado ainda',
    description: 'Cadastre o primeiro para começar a montar as partidas.',
    action: isAdmin ? <Button onClick={onCriar}>Novo jogador</Button> : undefined,
  }
}
