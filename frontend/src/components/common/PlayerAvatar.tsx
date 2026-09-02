import { useState } from 'react'

import { cn } from '@/lib/utils'

const TAMANHOS = {
  sm: 'h-10 w-10 text-sm',
  md: 'h-16 w-16 text-lg',
  lg: 'h-32 w-32 text-3xl',
} as const

interface PlayerAvatarProps {
  nickname: string
  /** Caminho relativo devolvido pela API, ex.: players/uuid.webp */
  photoPath?: string | null
  size?: keyof typeof TAMANHOS
  className?: string
}

/** Duas primeiras iniciais do apelido, para quem não tem foto. */
function iniciais(nickname: string): string {
  const partes = nickname.trim().split(/\s+/).filter(Boolean)
  if (partes.length === 0) return '?'
  if (partes.length === 1) return partes[0].slice(0, 2).toUpperCase()
  return (partes[0][0] + partes[1][0]).toUpperCase()
}

/**
 * Foto do jogador com anel laranja.
 *
 * Sem foto — ou se o arquivo não carregar — mostra as iniciais. Estado
 * previsto no design, não buraco na tela.
 */
export function PlayerAvatar({
  nickname,
  photoPath,
  size = 'md',
  className,
}: PlayerAvatarProps) {
  const [falhou, setFalhou] = useState(false)
  const mostrarFoto = Boolean(photoPath) && !falhou

  return (
    <div
      className={cn(
        'grid place-items-center overflow-hidden rounded-full border-2 border-primary bg-muted',
        TAMANHOS[size],
        className,
      )}
    >
      {mostrarFoto ? (
        <img
          src={`/media/${photoPath}`}
          alt={`Foto de ${nickname}`}
          onError={() => setFalhou(true)}
          className="h-full w-full object-cover"
          loading="lazy"
        />
      ) : (
        <span aria-hidden className="font-display font-extrabold text-muted-foreground">
          {iniciais(nickname)}
        </span>
      )}
    </div>
  )
}
