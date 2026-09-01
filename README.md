# SÓ NO MIGUÉ FC

**Futebol de segunda — Temporada 2026**

Aplicação web de estatísticas da pelada de quinta-feira. O site é público para
consulta; só o administrador registra partidas e jogadores.

> **Estado atual: Fase 2 concluída — infraestrutura.**
> Os três serviços sobem, conversam entre si e as migrations rodam. As telas
> ainda são placeholders navegáveis: jogadores, partidas, rankings, dashboard e
> autenticação chegam nas fases seguintes.

---

## Stack

| Camada | Tecnologias |
|---|---|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, React Router, TanStack Query, Recharts |
| Backend | Python 3.12, FastAPI, Pydantic, SQLAlchemy 2 (síncrono), Alembic |
| Banco | PostgreSQL 16 |
| Autenticação | JWT, um único administrador |
| Infra | Docker, Docker Compose |

---

## Como executar com Docker (recomendado)

Pré-requisitos: Docker e Docker Compose.

```bash
# 1. Configure o ambiente
cp .env.example .env
# Abra o .env e troque POSTGRES_PASSWORD, SECRET_KEY e ADMIN_PASSWORD.
# Para gerar uma chave:
#   python -c "import secrets; print(secrets.token_urlsafe(48))"

# 2. Suba tudo
docker compose up -d --build
```

Pronto:

| Serviço | Endereço |
|---|---|
| Aplicação | http://localhost:5173 |
| API | http://localhost:8000 |
| Documentação da API (Swagger) | http://localhost:8000/docs |
| Documentação alternativa (ReDoc) | http://localhost:8000/redoc |
| Saúde da API | http://localhost:8000/health |
| PostgreSQL | `localhost:5432` |

O backend aplica as migrations sozinho ao iniciar, então não há passo manual
entre subir e usar.

Comandos do dia a dia:

```bash
docker compose logs -f backend     # acompanhar o log
docker compose restart backend     # reiniciar um serviço
docker compose down                # parar (os dados continuam nos volumes)
docker compose down -v             # parar e APAGAR banco e fotos
```

---

## Migrations (Alembic)

Rodam automaticamente no start do backend. Para operá-las à mão:

```bash
# Estado atual e histórico
docker compose exec backend alembic current
docker compose exec backend alembic history

# Aplicar tudo que está pendente
docker compose exec backend alembic upgrade head

# Criar uma migration a partir dos models
docker compose exec backend alembic revision --autogenerate -m "descricao"

# Voltar uma revisão
docker compose exec backend alembic downgrade -1
```

A URL do banco **nunca** fica no `alembic.ini` (que é versionado): vem sempre de
`DATABASE_URL`, resolvida em `alembic/env.py`.

---

## Usuário administrador

> Disponível a partir da **Fase 4**.

As credenciais vêm do ambiente (`ADMIN_USERNAME` e `ADMIN_PASSWORD`) e nunca do
código. A senha é gravada com hash bcrypt — em texto puro ela não toca o banco,
o log nem o frontend.

```bash
docker compose exec backend python -m app.cli create-admin
```

O comando é idempotente: rodar de novo apenas atualiza a senha.

---

## Dados de desenvolvimento (seed)

> Disponível a partir da **Fase 7**.

```bash
docker compose exec backend python -m app.cli seed
```

Cria o administrador, alguns jogadores e algumas partidas **fictícios**,
claramente identificados como dados de desenvolvimento. Nunca rode em produção.

---

## Testes

```bash
docker compose exec backend pytest -v      # backend
docker compose exec frontend npm run typecheck   # tipos do frontend
```

Os testes das regras de negócio (vitória/empate/derrota, estatísticas,
rankings, edição e exclusão de partida) chegam na Fase 12.

---

## Executar sem Docker

<details>
<summary>Backend</summary>

Requer Python 3.12 e um PostgreSQL 16 acessível.

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# Aponte para o seu banco (note "localhost" no lugar de "db")
export DATABASE_URL="postgresql+psycopg://migue:senha@localhost:5432/migue"

alembic upgrade head
uvicorn app.main:app --reload
```
</details>

<details>
<summary>Frontend</summary>

Requer Node 20.

```bash
cd frontend
npm install
npm run dev
```

Fora do Docker o proxy do Vite cai em `http://localhost:8000` automaticamente.
Para apontar para outro lugar, defina `VITE_PROXY_TARGET`.
</details>

---

## Variáveis de ambiente

Todas ficam no `.env` da raiz, criado a partir do `.env.example`.
**O `.env` está no `.gitignore` e nunca deve ser versionado.**

| Variável | Para que serve |
|---|---|
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | Credenciais do Postgres |
| `POSTGRES_PORT` | Porta publicada no host (padrão 5432) |
| `DATABASE_URL` | Conexão usada pelo backend e pelo Alembic |
| `SECRET_KEY` | Assinatura dos tokens JWT |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Validade do token (padrão 720 = 12 h) |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` | Credenciais do administrador |
| `CORS_ORIGINS` | Origens permitidas, separadas por vírgula. Nunca `*` em produção |
| `MEDIA_ROOT` / `MEDIA_URL_PREFIX` | Onde as fotos são gravadas e sob qual caminho são servidas |
| `TZ` | Fuso horário (`America/Sao_Paulo`) |
| `CURRENT_SEASON` | Temporada exibida na interface |
| `VITE_API_URL` | Caminho base da API para o frontend |
| `VITE_PROXY_TARGET` | Alvo do proxy do Vite em desenvolvimento |

---

## Estrutura

```
futebol_quinta/
├── docker-compose.yml       db + backend + frontend
├── .env.example             modelo de configuração (versionado)
├── backend/
│   ├── app/
│   │   ├── core/            configuração, segurança, erros
│   │   ├── db/              engine, sessão, base declarativa
│   │   ├── models/          tabelas (Fase 3)
│   │   ├── schemas/         contratos de entrada e saída
│   │   ├── repositories/    acesso a dados e o SQL de estatísticas
│   │   ├── services/        regras de negócio
│   │   └── api/routers/     endpoints HTTP
│   ├── alembic/versions/    migrations
│   └── tests/
└── frontend/
    └── src/
        ├── api/             cliente HTTP — nenhum componente chama fetch direto
        ├── components/      layout, comuns e um diretório por domínio
        ├── hooks/           TanStack Query por recurso
        ├── pages/           uma por rota
        ├── routes/          roteador e navegação
        ├── lib/             utilidades e configuração do Query
        └── styles/          tokens do design system
```

A regra de camada do backend é rígida: **router não sabe SQL, repository não
sabe regra de negócio.** No frontend, componente nenhum chama `fetch`
diretamente — tudo passa por `src/api/client.ts`.

---

## Arquitetura em uma página

- **Quatro tabelas:** `players`, `matches`, `match_participations`, `users`.
- **Time não é entidade:** nome e placar ficam na partida; a participação guarda
  apenas o lado (1 ou 2).
- **Estatística nunca é armazenada:** jogos, vitórias, gols e assistências saem
  de uma consulta agregada sobre as partidas **realizadas**. Editar ou excluir
  uma partida corrige rankings e dashboard na leitura seguinte, sem recálculo.
- **Placar e gols individuais são independentes.** A soma dos gols anotados não
  precisa bater com o placar, e o sistema nunca bloqueia por causa disso.
- **Jogador não é apagado:** é inativado, e o histórico permanece intacto.
- **Temporada é o ano da data da partida** — sem tabela de temporadas no MVP.

---

## Roadmap

| Fase | Entrega | Estado |
|---|---|---|
| 0–1 | Requisitos, arquitetura, modelo de dados | ✅ |
| 2 | Estrutura do projeto e infraestrutura | ✅ |
| 3 | Models, migration do schema, repositories | — |
| 4 | Autenticação | — |
| 5 | Design system e layout | — |
| 6 | Jogadores | — |
| 7 | Partidas | — |
| 8 | Dashboard e gráficos | — |
| 9 | Rankings | — |
| 10 | Histórico e detalhes da partida | — |
| 11 | Refino visual e responsividade | — |
| 12 | Testes das regras de negócio | — |
| 13 | Documentação final | — |
