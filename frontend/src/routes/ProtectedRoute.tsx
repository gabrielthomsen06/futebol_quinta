import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { useAuth } from '@/hooks/useAuth'

/**
 * Barreira das rotas administrativas.
 *
 * Esconder ou bloquear tela não é segurança — quem souber o endereço pode
 * chamar a API direto. Quem protege é a dependência do backend; isto aqui só
 * evita mostrar um caminho que terminaria em 401.
 */
export function ProtectedRoute() {
  const { isAuthenticated, isLoading } = useAuth()
  const location = useLocation()

  if (isLoading) {
    return (
      <p role="status" className="py-16 text-center text-muted">
        Verificando sua sessão...
      </p>
    )
  }

  if (!isAuthenticated) {
    // Guarda o destino para voltar até aqui depois do login.
    return <Navigate to="/entrar" replace state={{ from: location }} />
  }

  return <Outlet />
}
