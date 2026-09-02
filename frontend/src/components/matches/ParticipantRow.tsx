import { X } from 'lucide-react'

import { PlayerAvatar } from '@/components/common/PlayerAvatar'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

export interface Escalado {
  player_id: string
  nickname: string
  photo_path: string | null
  team: 1 | 2
  goals: number
  assists: number
}

interface ParticipantRowProps {
  escalado: Escalado
  /** Gols e assistências só aparecem em partida realizada. */
  mostrarEstatisticas: boolean
  onChange: (campo: 'goals' | 'assists', valor: number) => void
  onRemove: () => void
}

/** Um jogador dentro de um time, com o que ele fez na partida. */
export function ParticipantRow({
  escalado,
  mostrarEstatisticas,
  onChange,
  onRemove,
}: ParticipantRowProps) {
  return (
    <li className="flex flex-wrap items-center gap-3 border-b border-border py-3 last:border-b-0">
      <PlayerAvatar
        nickname={escalado.nickname}
        photoPath={escalado.photo_path}
        size="sm"
      />
      <span className="min-w-0 flex-1 truncate font-medium">{escalado.nickname}</span>

      {mostrarEstatisticas && (
        <div className="flex items-center gap-2">
          <Campo
            id={`gols-${escalado.player_id}`}
            rotulo="Gols"
            valor={escalado.goals}
            onChange={(v) => onChange('goals', v)}
          />
          <Campo
            id={`assist-${escalado.player_id}`}
            rotulo="Assist."
            valor={escalado.assists}
            onChange={(v) => onChange('assists', v)}
          />
        </div>
      )}

      <Button
        type="button"
        variant="ghost"
        size="icon"
        onClick={onRemove}
        aria-label={`Tirar ${escalado.nickname} do time`}
      >
        <X aria-hidden />
      </Button>
    </li>
  )
}

function Campo({
  id,
  rotulo,
  valor,
  onChange,
}: {
  id: string
  rotulo: string
  valor: number
  onChange: (valor: number) => void
}) {
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={id} className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
        {rotulo}
      </label>
      <Input
        id={id}
        type="number"
        min={0}
        inputMode="numeric"
        value={valor}
        // Campo vazio vira 0 em vez de NaN: quem apaga o número para digitar
        // outro não pode ver a tela quebrar no meio da digitação.
        onChange={(e) => onChange(Math.max(0, Number(e.target.value) || 0))}
        className="h-11 min-h-11 w-16 px-2 text-center"
      />
    </div>
  )
}
