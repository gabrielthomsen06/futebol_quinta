import { Link, NavLink, useNavigate } from 'react-router-dom'

import { BrandMark } from '@/components/layout/BrandMark'
import { Button } from '@/components/ui/button'
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
    <header className="sticky top-0 z-20 hidden border-b border-border bg-muted/95 backdrop-blur md:block">
      <div className="mx-auto flex h-16 max-w-6xl items-center gap-8 px-6">
        <Link to="/" className="rounded-control">
          <BrandMark withWordmark />
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
                  isActive ? 'text-primary-hi' : 'text-muted-foreground hover:text-foreground',
                )
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="ml-auto">
          {isAuthenticated ? (
            <Button variant="ghost" size="sm" onClick={sair}>
              Sair
            </Button>
          ) : (
            <Button asChild variant="outline" size="sm">
              <Link to="/entrar">Entrar</Link>
            </Button>
          )}
        </div>
      </div>
    </header>
  )
}
