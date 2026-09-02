import { Slot } from '@radix-ui/react-slot'
import { cva, type VariantProps } from 'class-variance-authority'
import { forwardRef, type ButtonHTMLAttributes } from 'react'

import { cn } from '@/lib/utils'

/**
 * Altura mínima de 44px em todas as variantes: é o alvo de toque confortável
 * no celular, que é onde a maioria vai usar o app.
 */
const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-control font-display font-bold uppercase tracking-widest transition-colors disabled:pointer-events-none disabled:opacity-60 [&_svg]:size-4 [&_svg]:shrink-0',
  {
    variants: {
      variant: {
        primary: 'bg-primary text-primary-foreground hover:bg-primary-hi',
        outline:
          'border border-primary text-primary-hi hover:bg-primary hover:text-primary-foreground',
        ghost: 'text-muted-foreground hover:bg-muted hover:text-foreground',
        // Vermelho só no contorno: excluir é raro, e um botão vermelho sólido
        // puxaria a atenção da tela inteira para a ação mais perigosa.
        destructive:
          'border border-destructive text-destructive hover:bg-destructive hover:text-destructive-foreground',
      },
      size: {
        default: 'min-h-11 px-5 text-base',
        sm: 'min-h-11 px-3 text-label',
        lg: 'min-h-12 px-6 text-lg',
        icon: 'min-h-11 w-11',
      },
    },
    defaultVariants: { variant: 'primary', size: 'default' },
  },
)

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  /** Renderiza o filho no lugar do <button>, mantendo o estilo (ex.: um Link). */
  asChild?: boolean
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : 'button'
    return (
      <Comp className={cn(buttonVariants({ variant, size }), className)} ref={ref} {...props} />
    )
  },
)
Button.displayName = 'Button'

export { buttonVariants }
