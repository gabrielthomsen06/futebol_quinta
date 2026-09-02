import { useState, type FormEvent } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'

import { ApiError } from '@/api/client'
import { PageHeader } from '@/components/common/PageHeader'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
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
    <section className="mx-auto max-w-sm">
      <PageHeader
        eyebrow="Área do administrador"
        title="Entrar"
        description="Só o administrador precisa entrar. Consultar rankings, histórico e jogadores é livre."
      />

      <form onSubmit={aoEnviar} className="flex flex-col gap-5">
        <div className="flex flex-col gap-2">
          <label
            htmlFor="username"
            className="text-label font-semibold uppercase text-muted-foreground"
          >
            Usuário
          </label>
          <Input
            id="username"
            name="username"
            autoComplete="username"
            required
            invalid={erro !== null}
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
        </div>

        <div className="flex flex-col gap-2">
          <label
            htmlFor="password"
            className="text-label font-semibold uppercase text-muted-foreground"
          >
            Senha
          </label>
          <Input
            id="password"
            name="password"
            type="password"
            autoComplete="current-password"
            required
            invalid={erro !== null}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>

        {erro && (
          <p
            role="alert"
            className="rounded-control border border-destructive px-4 py-3 text-sm text-destructive"
          >
            {erro}
          </p>
        )}

        <Button type="submit" size="lg" disabled={entrando}>
          {entrando ? 'Entrando...' : 'Entrar'}
        </Button>
      </form>
    </section>
  )
}
