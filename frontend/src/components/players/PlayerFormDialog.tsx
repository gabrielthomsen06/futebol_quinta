import { useEffect, useState, type FormEvent } from 'react'

import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import type { PlayerWithStats } from '@/types/api'

interface PlayerFormDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  /** Nulo cria; preenchido edita. */
  player: PlayerWithStats | null
  onSubmit: (nickname: string) => Promise<void>
  pending: boolean
  /** Mensagem vinda da API, por exemplo apelido já usado. */
  error: string | null
}

/**
 * Criar e editar jogador.
 *
 * Um jogador é só apelido — nem posição, nem número, nem idade —, então o
 * formulário é um campo. A foto tem fluxo próprio, no perfil.
 */
export function PlayerFormDialog({
  open,
  onOpenChange,
  player,
  onSubmit,
  pending,
  error,
}: PlayerFormDialogProps) {
  const [nickname, setNickname] = useState('')

  // Reabrir o diálogo precisa mostrar o valor certo: em branco para criar,
  // o apelido atual para editar.
  useEffect(() => {
    if (open) setNickname(player?.nickname ?? '')
  }, [open, player])

  async function aoEnviar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    await onSubmit(nickname.trim())
  }

  const editando = player !== null

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{editando ? 'Editar jogador' : 'Novo jogador'}</DialogTitle>
          <DialogDescription>
            {editando
              ? 'O histórico e as estatísticas continuam os mesmos.'
              : 'Só o apelido. A foto você adiciona depois, no perfil.'}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={aoEnviar} className="flex flex-col gap-2">
          <label
            htmlFor="nickname"
            className="text-label font-semibold uppercase text-muted-foreground"
          >
            Apelido
          </label>
          <Input
            id="nickname"
            value={nickname}
            onChange={(e) => setNickname(e.target.value)}
            maxLength={40}
            required
            autoFocus
            invalid={error !== null}
            placeholder="Como ele é chamado na pelada"
          />

          {error && (
            <p role="alert" className="mt-1 text-sm text-destructive">
              {error}
            </p>
          )}

          <DialogFooter>
            <Button
              type="button"
              variant="ghost"
              onClick={() => onOpenChange(false)}
              disabled={pending}
            >
              Cancelar
            </Button>
            <Button type="submit" disabled={pending || nickname.trim() === ''}>
              {pending ? 'Salvando...' : 'Salvar'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
