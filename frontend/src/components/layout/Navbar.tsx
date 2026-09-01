import { Link, NavLink, useNavigate } from 'react-router-dom'

import { useAuth } from '@/hooks/useAuth'
import { cn } from '@/lib/utils'
import { NAV_ITEMS } from '@/routes/navigation'

/** Navegação de desktop. No celular quem manda é a barra inferior. */
export function Navbar() {
  const { isAuthenticated, logout } = useAuth()
  const navigate = useNavigate()

  function sair() {
    logout()
    navigate('/', { replace: true })
  }

  return (
    <header className="sticky top-0 z-20 hidden border-b border-line bg-surface/95 backdrop-blur md:block">
      <div className="mx-auto flex h-16 max-w-6xl items-center gap-8 px-6">
        <Link to="/" className="flex items-center gap-3">
          <span
            aria-hidden
            className="grid h-9 w-9 place-items-center rounded-full border-2 border-fg font-display text-sm font-extrabold"
          >
            SM
          </span>
          <span className="font-display text-xl font-extrabold uppercase tracking-wider">
            Só no Migué FC
          </span>
        </Link>

        <nav aria-label="Navegação principal" className="flex items-center gap-1">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                cn(
                  'rounded-control px-3 py-2 text-sm font-medium transition-colors',
                  isActive ? 'text-accent-hi' : 'text-muted hover:text-fg',
                )
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        {isAuthenticated ? (
          <button
            type="button"
            onClick={sair}
            className="ml-auto min-h-11 rounded-control border border-line px-4 text-label font-semibold uppercase tracking-widest text-muted transition-colors hover:border-accent hover:text-accent-hi"
          >
            Sair
          </button>
        ) : (
          <Link
            to="/entrar"
            className="ml-auto flex min-h-11 items-center rounded-control border border-accent px-4 text-label font-semibold uppercase tracking-widest text-accent-hi transition-colors hover:bg-accent hover:text-ink"
          >
            Entrar
          </Link>
        )}
      </div>
    </header>
  )
}
