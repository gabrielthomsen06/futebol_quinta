import { Toaster as Sonner, toast } from 'sonner'

/**
 * Toasts do app, montados uma única vez no AppShell.
 *
 * As cores vêm dos nossos tokens em vez do tema embutido do sonner, para o
 * aviso não destoar do resto da interface.
 */
export function Toaster() {
  return (
    <Sonner
      theme="dark"
      position="top-center"
      // Fica acima da barra de navegação inferior do celular.
      offset={16}
      toastOptions={{
        classNames: {
          toast:
            'group rounded-card border border-border bg-card text-foreground shadow-2xl',
          description: 'text-muted-foreground',
          actionButton: 'bg-primary text-primary-foreground',
          cancelButton: 'bg-muted text-muted-foreground',
          error: 'border-destructive',
        },
      }}
    />
  )
}

export { toast }
