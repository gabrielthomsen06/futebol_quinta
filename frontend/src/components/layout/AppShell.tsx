import { Outlet } from 'react-router-dom'

import { MobileNav } from '@/components/layout/MobileNav'
import { Navbar } from '@/components/layout/Navbar'
import { Toaster } from '@/components/ui/toaster'

/** Moldura da aplicação: navbar no desktop, barra inferior no celular. */
export function AppShell() {
  return (
    <div className="min-h-dvh bg-background">
      {/* Sem isto, quem navega por teclado atravessa a navegação inteira
          em cada página antes de chegar ao conteúdo. */}
      <a
        href="#conteudo"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-control focus:bg-primary focus:px-4 focus:py-2 focus:font-display focus:uppercase focus:text-primary-foreground"
      >
        Pular para o conteúdo
      </a>

      <Navbar />
      <main
        id="conteudo"
        className="mx-auto max-w-6xl px-5 pb-[calc(theme(spacing.nav)+2rem)] pt-6 md:px-6 md:pb-16"
      >
        <Outlet />
      </main>
      <MobileNav />
      <Toaster />
    </div>
  )
}
