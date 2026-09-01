import path from 'node:path'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Dentro do compose o backend é alcançado pelo nome do serviço.
// Rodando na máquina, cai no localhost.
const proxyTarget = process.env.VITE_PROXY_TARGET ?? 'http://localhost:8000'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { '@': path.resolve(__dirname, './src') },
  },
  server: {
    host: true,
    port: 5173,
    strictPort: true,
    // Bind mount do Windows não propaga eventos de arquivo para o container.
    watch: { usePolling: true, interval: 300 },
    proxy: {
      // O navegador fala só com o Vite; ele repassa para a API.
      // Assim não existe requisição cross-origin em desenvolvimento.
      '/api': { target: proxyTarget, changeOrigin: true },
      '/media': { target: proxyTarget, changeOrigin: true },
    },
  },
})
