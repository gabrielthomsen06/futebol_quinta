import type { HTMLAttributes } from 'react'

import { cn } from '@/lib/utils'

/**
 * Bloco pulsante com a forma do conteúdo que vai chegar.
 *
 * Preferido ao spinner: mantém o layout estável e evita o pulo da página
 * quando o dado chega.
 */
export function Skeleton({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      aria-hidden
      className={cn('animate-pulse rounded-control bg-muted', className)}
      {...props}
    />
  )
}
