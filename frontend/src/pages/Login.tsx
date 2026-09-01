import { useState, type FormEvent } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'

import { ApiError } from '@/api/client'
import { useAuth } from '@/hooks/useAuth'

interface EstadoDeOrigem {
  from?: { pathname?: string }
}

export function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [erro, setErro] = useState<string | null>(null)
  const [entrando, setEntrando] = useState(false)

  const destino = (location.state as EstadoDeOrigem | null)?.from?.pathname ?? '/'

  async function aoEnviar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    setErro(null)
    setEntrando(true)
    try {
      await login(username, password)
      navigate(destino, { replace: true })
    } catch (falha) {
      // A mensagem vem do servidor: para senha errada e usuário inexistente
      // ela é a mesma, de propósito.
      setErro(
        falha instanceof ApiError ? falha.message : 'Não foi possível entrar. Tente de novo.',
      )
    } finally {
      setEntrando(false)
    }
  }

  return (
    <section className="mx-auto max-w-sm py-10">
      <p className="text-label font-semibold uppercase tracking-[0.2em] text-accent">
        Área do administrador
      </p>
      <h1 className="mt-2 font-display text-4xl font-extrabold uppercase tracking-wide">Entrar</h1>
      <p className="mt-3 text-muted">
        Só o administrador precisa entrar. Consultar rankings, histórico e jogadores é livre.
      </p>

      <form onSubmit={aoEnviar} className="mt-8 flex flex-col gap-5">
        <div className="flex flex-col gap-2">
          <label htmlFor="username" className="text-label font-semibold uppercase tracking-widest text-muted">
            Usuário
          </label>
          <input
            id="username"
            name="username"
            autoComplete="username"
            required
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="min-h-12 rounded-control border border-line bg-card px-4 text-fg placeholder:text-dim"
          />
        </div>

        <div className="flex flex-col gap-2">
          <label htmlFor="password" className="text-label font-semibold uppercase tracking-widest text-muted">
            Senha
          </label>
          <input
            id="password"
            name="password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="min-h-12 rounded-control border border-line bg-card px-4 text-fg placeholder:text-dim"
          />
        </div>

        {erro && (
          <p role="alert" className="rounded-control border border-red-900/60 bg-red-950/30 px-4 py-3 text-sm text-red-300">
            {erro}
          </p>
        )}

        <button
          type="submit"
          disabled={entrando}
          className="min-h-12 rounded-control bg-accent px-5 font-display text-lg font-bold uppercase tracking-widest text-ink transition-colors hover:bg-accent-hi disabled:opacity-60"
        >
          {entrando ? 'Entrando...' : 'Entrar'}
        </button>
      </form>
    </section>
  )
}
