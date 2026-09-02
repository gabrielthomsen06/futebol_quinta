import { AlertTriangle } from 'lucide-react'

import { Button } from '@/components/ui/button'

interface ErrorStateProps {
  /** Mensagem que o servidor mandou em "detail". */
  message?: string
  onRetry?: () => void
  retrying?: boolean
}

/**
 * Algo falhou.
 *
 * A mensagem exibida é a que a API devolveu — ela já vem legível desde a
 * Fase 2, então traduzir código de erro aqui seria refazer trabalho e piorar.
 */
export function ErrorState({ message, onRetry, retrying = false }: ErrorStateProps) {
  return (
    <div
      role="alert"
      className="flex flex-col items-center gap-3 rounded-card border border-border bg-card px-6 py-12 text-center"
    >
      <AlertTriangle aria-hidden className="h-8 w-8 text-destructive" />
      <p className="font-display text-xl uppercase tracking-wide">Não foi possível carregar</p>
      <p className="max-w-sm text-sm text-muted-foreground">
        {message ?? 'Tente de novo em instantes.'}
      </p>
      {onRetry && (
        <Button variant="outline" size="sm" onClick={onRetry} disabled={retrying} className="mt-2">
          {retrying ? 'Tentando...' : 'Tentar de novo'}
        </Button>
      )}
    </div>
  )
}
