import { CalendarDays, Goal, Trophy, Users } from 'lucide-react'
import type { ReactNode } from 'react'

import { ConfirmDialog } from '@/components/common/ConfirmDialog'
import { EmptyState } from '@/components/common/EmptyState'
import { ErrorState } from '@/components/common/ErrorState'
import { LoadingState } from '@/components/common/LoadingState'
import { PageHeader } from '@/components/common/PageHeader'
import { PlayerAvatar } from '@/components/common/PlayerAvatar'
import { StatCard } from '@/components/common/StatCard'
import { StatusBadge } from '@/components/common/StatusBadge'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { toast } from '@/components/ui/toaster'

/**
 * Vitrine do design system, fora da navegação.
 *
 * Existe para revisão visual: reúne num lugar só os componentes e os três
 * estados, de modo que a identidade possa ser aprovada antes de as Fases 6 a
 * 10 construírem em cima dela. Não usa dado real — os valores são fictícios e
 * estão aqui apenas para dar forma aos componentes.
 */
function Bloco({ titulo, children }: { titulo: string; children: ReactNode }) {
  return (
    <section className="border-t border-border py-8">
      <h2 className="mb-5 font-display text-section uppercase text-gold">{titulo}</h2>
      {children}
    </section>
  )
}

const TOKENS = [
  ['background', '#0A0A0A', 'bg-background'],
  ['muted', '#121110', 'bg-muted'],
  ['card', '#1A1715', 'bg-card'],
  ['border', '#2E2825', 'bg-border'],
  ['subtle-foreground', '#8A8078', 'bg-subtle-foreground'],
  ['muted-foreground', '#9C938B', 'bg-muted-foreground'],
  ['foreground', '#F6F2ED', 'bg-foreground'],
  ['primary', '#F26B21', 'bg-primary'],
  ['primary-hi', '#FF9A4D', 'bg-primary-hi'],
  ['gold', '#F2B33D', 'bg-gold'],
  ['destructive', '#E5484D', 'bg-destructive'],
] as const

export function DesignSystemPage() {
  return (
    <div className="pb-10">
      <PageHeader
        eyebrow="Fase 5"
        title="Design system"
        description="Página de revisão, fora da navegação. Os números são fictícios."
      />

      <Bloco titulo="Cores">
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
          {TOKENS.map(([nome, hex, classe]) => (
            <div key={nome} className="overflow-hidden rounded-card border border-border">
              <div className={`h-14 ${classe}`} />
              <div className="px-3 py-2">
                <p className="text-xs font-semibold uppercase tracking-wider">{nome}</p>
                <p className="tabular text-xs text-muted-foreground">{hex}</p>
              </div>
            </div>
          ))}
        </div>
      </Bloco>

      <Bloco titulo="Tipografia">
        <div className="flex flex-col gap-4 rounded-card border border-border bg-card p-5">
          <p className="tabular font-display text-stat-xl text-primary">5 x 3</p>
          <p className="tabular font-display text-stat text-primary">42</p>
          <p className="font-display text-title uppercase tracking-wide">Título de página</p>
          <p className="font-display text-section uppercase text-gold">Rótulo de seção</p>
          <p className="text-base">
            Texto corrido em Inter. A soma dos gols individuais não precisa bater com o placar.
          </p>
          <p className="text-label font-semibold uppercase text-muted-foreground">
            Rótulo de campo
          </p>
          <p className="text-sm text-subtle-foreground">
            Texto terciário, agora em #8A8078 para passar no contraste.
          </p>
        </div>
      </Bloco>

      <Bloco titulo="Botões">
        <div className="flex flex-wrap items-center gap-3">
          <Button>Salvar partida</Button>
          <Button variant="outline">Entrar</Button>
          <Button variant="ghost">Cancelar</Button>
          <Button variant="destructive">Excluir</Button>
          <Button disabled>Salvando...</Button>
          <Button size="sm" variant="outline">
            Pequeno
          </Button>
        </div>
      </Bloco>

      <Bloco titulo="Estatísticas e status">
        <div className="grid grid-cols-3 gap-3">
          <StatCard value={24} label="Partidas" icon={CalendarDays} />
          <StatCard value={87} label="Gols registrados" icon={Goal} highlight />
          <StatCard value={52} label="Assistências" icon={Trophy} />
        </div>
        <div className="mt-4 flex flex-wrap gap-3">
          <StatusBadge status="SCHEDULED" />
          <StatusBadge status="PLAYED" />
          <StatusBadge status="CANCELLED" />
        </div>
      </Bloco>

      <Bloco titulo="Jogador sem foto">
        <div className="flex items-end gap-4">
          <PlayerAvatar nickname="Gabriel" size="sm" />
          <PlayerAvatar nickname="João Pedro" size="md" />
          <PlayerAvatar nickname="Carlos" size="lg" />
        </div>
      </Bloco>

      <Bloco titulo="Campos">
        <div className="flex max-w-sm flex-col gap-4">
          <div className="flex flex-col gap-2">
            <label htmlFor="ex-apelido" className="text-label font-semibold uppercase text-muted-foreground">
              Apelido
            </label>
            <Input id="ex-apelido" defaultValue="Gabriel" />
          </div>
          <div className="flex flex-col gap-2">
            <label htmlFor="ex-erro" className="text-label font-semibold uppercase text-muted-foreground">
              Campo com erro
            </label>
            <Input id="ex-erro" invalid defaultValue="" placeholder="Obrigatório" />
          </div>
        </div>
      </Bloco>

      <Bloco titulo="Retorno de ação">
        <div className="flex flex-wrap gap-3">
          <Button variant="outline" onClick={() => toast.success('Partida salva')}>
            Toast de sucesso
          </Button>
          <Button
            variant="outline"
            onClick={() => toast.error('Usuário ou senha inválidos.')}
          >
            Toast de erro
          </Button>

          <Dialog>
            <DialogTrigger asChild>
              <Button variant="outline">Abrir diálogo</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Novo jogador</DialogTitle>
                <DialogDescription>
                  Exemplo do diálogo que a Fase 6 vai usar para criar e editar jogador.
                </DialogDescription>
              </DialogHeader>
              <Input placeholder="Apelido" />
              <DialogFooter>
                <Button variant="ghost">Cancelar</Button>
                <Button>Salvar</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>

          <ConfirmDialog
            trigger={<Button variant="destructive">Excluir partida</Button>}
            title="Excluir a partida?"
            description="04/09/2026 — TIME 1 5 x 3 BRANCO, com 6 jogadores. As estatísticas dela somem dos rankings e dos perfis. Não dá para desfazer."
            onConfirm={() => toast.success('Partida excluída')}
          />
        </div>
      </Bloco>

      <Bloco titulo="Carregando">
        <LoadingState variant="stats" />
        <div className="mt-4">
          <LoadingState variant="list" rows={3} />
        </div>
      </Bloco>

      <Bloco titulo="Vazio">
        <EmptyState
          icon={Users}
          title="Nenhum jogador cadastrado ainda"
          description="Quando você cadastrar o primeiro, ele aparece aqui."
          action={<Button variant="outline">Novo jogador</Button>}
        />
      </Bloco>

      <Bloco titulo="Erro">
        <ErrorState
          message="Não foi possível falar com o servidor. Verifique sua conexão."
          onRetry={() => toast.message('Tentaria de novo')}
        />
      </Bloco>

      <Bloco titulo="Esqueleto solto">
        <div className="flex flex-col gap-2">
          <Skeleton className="h-8 w-1/3" />
          <Skeleton className="h-4 w-2/3" />
          <Skeleton className="h-4 w-1/2" />
        </div>
      </Bloco>
    </div>
  )
}
