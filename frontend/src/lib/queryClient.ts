import { QueryClient } from '@tanstack/react-query'

/**
 * Configuração global do TanStack Query.
 *
 * Os dados da pelada mudam uma vez por semana, então vale manter em cache por
 * um bom tempo e não refazer requisição a cada troca de aba — trocar de página
 * não deve custar rede.
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60_000,
      gcTime: 5 * 60_000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: 0,
    },
  },
})

/**
 * Chaves de cache centralizadas, para a invalidação após mutation não errar o
 * alvo. Todas as de jogador começam com 'players', então invalidar esse
 * prefixo atinge a listagem e os perfis de uma vez.
 */
export const queryKeys = {
  health: ['health'] as const,
  players: ['players'] as const,
  playerList: (status: string) => ['players', 'list', status] as const,
  player: (id: string) => ['players', 'detail', id] as const,
  playerStats: (id: string) => ['players', 'stats', id] as const,
}
