import { Link } from 'react-router-dom'

export function NotFoundPage() {
  return (
    <section className="py-16 text-center">
      <p className="font-display text-6xl font-extrabold text-accent">404</p>
      <h1 className="mt-2 font-display text-3xl font-extrabold uppercase tracking-wide">
        Página não encontrada
      </h1>
      <p className="mt-3 text-muted">O endereço que você abriu não existe nesta aplicação.</p>
      <Link
        to="/"
        className="mt-8 inline-flex min-h-11 items-center rounded-control border border-accent px-5 text-label font-semibold uppercase tracking-widest text-accent-hi transition-colors hover:bg-accent hover:text-ink"
      >
        Voltar ao início
      </Link>
    </section>
  )
}
