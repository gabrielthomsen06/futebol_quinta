import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'

interface LoadingStateProps {
  /** Forma do conteúdo que está chegando. */
  variant?: 'list' | 'cards' | 'stats'
  rows?: number
  className?: string
}

/**
 * Espera com a forma do que vem depois.
 *
 * Um spinner centralizado apaga a página inteira e faz a espera parecer mais
 * longa; o esqueleto mantém o layout no lugar e evita o pulo quando o dado
 * chega. O aviso para leitor de tela é textual, já que o desenho é decorativo.
 */
export function LoadingState({ variant = 'list', rows = 5, className }: LoadingStateProps) {
  return (
    <div className={cn('w-full', className)}>
      <span role="status" className="sr-only">
        Carregando...
      </span>

      {variant === 'stats' && (
        <div className="grid grid-cols-3 gap-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-28" />
          ))}
        </div>
      )}

      {variant === 'cards' && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: rows }).map((_, i) => (
            <Skeleton key={i} className="h-64" />
          ))}
        </div>
      )}

      {variant === 'list' && (
        <div className="flex flex-col gap-2">
          {Array.from({ length: rows }).map((_, i) => (
            <Skeleton key={i} className="h-16" />
          ))}
        </div>
      )}
    </div>
  )
}
