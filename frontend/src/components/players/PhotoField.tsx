import { ImageUp, Trash2 } from 'lucide-react'
import { useRef, type ChangeEvent } from 'react'

import { ConfirmDialog } from '@/components/common/ConfirmDialog'
import { Button } from '@/components/ui/button'
import type { Player } from '@/types/api'

/** Espelha o limite do backend, para avisar antes de gastar upload. */
const MAX_BYTES = 5 * 1024 * 1024
const ACEITOS = 'image/jpeg,image/png,image/webp'

interface PhotoFieldProps {
  player: Pick<Player, 'nickname' | 'photo_path'>
  onUpload: (arquivo: File) => void
  onRemove: () => void
  onReject: (mensagem: string) => void
  pending: boolean
}

/**
 * Troca e remoção da foto, no perfil.
 *
 * Sem editor de recorte: o servidor recorta o quadrado central e devolve um
 * WEBP 512×512. O tamanho é conferido aqui também — recusar 20 MB depois de
 * subir o arquivo inteiro seria desperdiçar o tempo de quem está no celular.
 */
export function PhotoField({
  player,
  onUpload,
  onRemove,
  onReject,
  pending,
}: PhotoFieldProps) {
  const input = useRef<HTMLInputElement>(null)

  function aoEscolher(evento: ChangeEvent<HTMLInputElement>) {
    const arquivo = evento.target.files?.[0]
    // Permite escolher o mesmo arquivo de novo depois de um erro.
    evento.target.value = ''
    if (!arquivo) return

    if (arquivo.size > MAX_BYTES) {
      onReject('A foto precisa ter no máximo 5 MB.')
      return
    }
    if (!ACEITOS.split(',').includes(arquivo.type)) {
      onReject(
        arquivo.type === 'image/heic' || arquivo.name.toLowerCase().endsWith('.heic')
          ? 'Fotos HEIC (padrão do iPhone) não são aceitas. Converta para JPEG.'
          : 'Envie um arquivo JPEG, PNG ou WEBP.',
      )
      return
    }
    onUpload(arquivo)
  }

  return (
    <div className="flex flex-wrap items-center gap-2">
      <input
        ref={input}
        type="file"
        accept={ACEITOS}
        onChange={aoEscolher}
        className="sr-only"
        aria-label={`Escolher foto de ${player.nickname}`}
      />

      <Button
        variant="outline"
        size="sm"
        onClick={() => input.current?.click()}
        disabled={pending}
      >
        <ImageUp aria-hidden />
        {pending ? 'Enviando...' : player.photo_path ? 'Trocar foto' : 'Adicionar foto'}
      </Button>

      {player.photo_path && (
        <ConfirmDialog
          trigger={
            <Button variant="ghost" size="sm" disabled={pending}>
              <Trash2 aria-hidden />
              Remover
            </Button>
          }
          title="Remover a foto?"
          description={`A foto de ${player.nickname} será apagada e o card volta a mostrar as iniciais. As estatísticas não mudam.`}
          confirmLabel="Remover"
          onConfirm={onRemove}
          loading={pending}
        />
      )}
    </div>
  )
}
