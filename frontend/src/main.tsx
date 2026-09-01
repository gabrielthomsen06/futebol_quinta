import { QueryClientProvider } from '@tanstack/react-query'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { RouterProvider } from 'react-router-dom'

import { AuthProvider } from '@/contexts/AuthContext'
import { queryClient } from '@/lib/queryClient'
import { router } from '@/routes/router'
import '@/styles/index.css'

const container = document.getElementById('root')
if (!container) {
  throw new Error('Elemento #root não encontrado no index.html')
}

createRoot(container).render(
  <StrictMode>
    {/* AuthProvider dentro do QueryClientProvider: ao sair, ele limpa o cache. */}
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <RouterProvider router={router} />
      </AuthProvider>
    </QueryClientProvider>
  </StrictMode>,
)
