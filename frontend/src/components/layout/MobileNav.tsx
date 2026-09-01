import { NavLink } from 'react-router-dom'

import { cn } from '@/lib/utils'
import { NAV_ITEMS } from '@/routes/navigation'

/**
 * Barra inferior fixa do celular: quatro alvos grandes, alcançáveis com o polegar.
 * O estado ativo não depende só da cor — o ícone e o rótulo mudam de peso junto.
 */
export function MobileNav() {
  return (
    <nav
      aria-label="Navegação principal"
      className="fixed inset-x-0 bottom-0 z-20 border-t border-line bg-surface/95 pb-[env(safe-area-inset-bottom)] backdrop-blur md:hidden"
    >
      <ul className="mx-auto flex h-nav max-w-lg items-stretch">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon
          return (
            <li key={item.to} className="flex-1">
              <NavLink
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  cn(
                    'flex h-full flex-col items-center justify-center gap-1 text-[11px] transition-colors',
                    isActive ? 'font-semibold text-accent-hi' : 'text-muted',
                  )
                }
              >
                <Icon aria-hidden className="h-5 w-5" />
                {item.label}
              </NavLink>
            </li>
          )
        })}
      </ul>
    </nav>
  )
}
