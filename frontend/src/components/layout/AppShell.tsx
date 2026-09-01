import { Outlet } from 'react-router-dom'

import { MobileNav } from '@/components/layout/MobileNav'
import { Navbar } from '@/components/layout/Navbar'

/**
 * Moldura da aplicação: navbar no desktop, barra inferior no celular.
 * O visual definitivo é trabalho da Fase 5 — aqui existe o mínimo para navegar.
 */
export function AppShell() {
  return (
    <div className="min-h-dvh bg-ink">
      <Navbar />
      <main className="mx-auto max-w-6xl px-5 pb-[calc(theme(spacing.nav)+2rem)] pt-6 md:px-6 md:pb-16">
        <Outlet />
      </main>
      <MobileNav />
    </div>
  )
}
