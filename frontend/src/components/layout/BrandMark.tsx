import { cn } from '@/lib/utils'

const TAMANHOS = { sm: 'h-8 w-8', md: 'h-9 w-9', lg: 'h-12 w-12' } as const

interface BrandMarkProps {
  size?: keyof typeof TAMANHOS
  /** Mostra "SÓ NO MIGUÉ FC" ao lado do símbolo. */
  withWordmark?: boolean
  className?: string
}

/**
 * A marca do clube.
 *
 * O arquivo servido tem 96px e ~2 KB, gerado a partir do original de 4000px e
 * 1,3 MB — peso que não faz sentido carregar num cabeçalho.
 */
export function BrandMark({ size = 'md', withWordmark = false, className }: BrandMarkProps) {
  return (
    <span className={cn('flex items-center gap-3', className)}>
      <img
        src="/logo.webp"
        alt="Escudo do Só no Migué FC"
        width={96}
        height={96}
        className={cn('rounded-full', TAMANHOS[size])}
      />
      {withWordmark && (
        <span className="font-display text-xl font-extrabold uppercase tracking-wider">
          Só no Migué FC
        </span>
      )}
    </span>
  )
}
