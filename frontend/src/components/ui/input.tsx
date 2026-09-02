import { forwardRef, type InputHTMLAttributes } from 'react'

import { cn } from '@/lib/utils'

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  /** Marca o campo como inválido para o leitor de tela e para o estilo. */
  invalid?: boolean
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, invalid, ...props }, ref) => (
    <input
      ref={ref}
      aria-invalid={invalid || undefined}
      className={cn(
        'min-h-12 w-full rounded-control border border-input bg-card px-4 text-foreground',
        'placeholder:text-subtle-foreground disabled:opacity-60',
        // Números de estatística alinhados e sem as setinhas do navegador,
        // que atrapalham em campo pequeno de celular.
        '[&[type=number]]:tabular [&[type=number]]:[appearance:textfield]',
        '[&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none',
        invalid && 'border-destructive',
        className,
      )}
      {...props}
    />
  ),
)
Input.displayName = 'Input'
