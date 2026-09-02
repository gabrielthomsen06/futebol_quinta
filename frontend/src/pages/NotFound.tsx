import { Link } from 'react-router-dom'

import { Button } from '@/components/ui/button'

export function NotFoundPage() {
  return (
    <section className="py-16 text-center">
      <p className="tabular font-display text-stat-xl text-primary">404</p>
      <h1 className="mt-2 font-display text-title uppercase tracking-wide">
        Página não encontrada
      </h1>
      <p className="mt-3 text-muted-foreground">
        O endereço que você abriu não existe nesta aplicação.
      </p>
      <Button asChild variant="outline" className="mt-8">
        <Link to="/">Voltar ao início</Link>
      </Button>
    </section>
  )
}
