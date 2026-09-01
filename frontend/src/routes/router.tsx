import { createBrowserRouter } from 'react-router-dom'

import { AppShell } from '@/components/layout/AppShell'
import { HistoryPage } from '@/pages/History'
import { HomePage } from '@/pages/Home'
import { LoginPage } from '@/pages/Login'
import { MatchDetailPage } from '@/pages/MatchDetail'
import { MatchFormPage } from '@/pages/MatchForm'
import { NotFoundPage } from '@/pages/NotFound'
import { PlayerProfilePage } from '@/pages/PlayerProfile'
import { PlayersPage } from '@/pages/Players'
import { RankingsPage } from '@/pages/Rankings'

/**
 * URLs em português, iguais às da interface, e estáveis: /partidas/:id é o link
 * que alguém cola no grupo para mostrar o jogo de quinta.
 *
 * As rotas administrativas (/partidas/nova e /partidas/:id/editar) ganham a
 * proteção do ProtectedRoute na Fase 4 — hoje já existem para o roteamento
 * ficar completo.
 */
export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppShell />,
    children: [
      { index: true, element: <HomePage /> },
      { path: 'rankings', element: <RankingsPage /> },
      { path: 'historico', element: <HistoryPage /> },
      { path: 'partidas/nova', element: <MatchFormPage /> },
      { path: 'partidas/:id', element: <MatchDetailPage /> },
      { path: 'partidas/:id/editar', element: <MatchFormPage /> },
      { path: 'jogadores', element: <PlayersPage /> },
      { path: 'jogadores/:id', element: <PlayerProfilePage /> },
      { path: 'entrar', element: <LoginPage /> },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
])
