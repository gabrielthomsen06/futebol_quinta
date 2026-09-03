# SÓ NO MIGUÉ FC

**Futebol de segunda — Temporada 2026**

Aplicação web de estatísticas da pelada de quinta-feira. O site é público para
consulta; só o administrador registra partidas e jogadores.

> **Estado atual: Fase 11 concluída — pronto para produção.**
> Todas as telas públicas estão prontas (início, rankings, histórico, detalhes da
> partida, jogadores e perfil) mais o CRUD administrativo. A Fase 11 acrescentou a
> stack de produção, backup fora da VPS e os smoke tests — veja
> [Deploy em produção](#deploy-em-produção).

---

## Stack

| Camada | Tecnologias |
|---|---|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, React Router, TanStack Query, Recharts |
| Backend | Python 3.12, FastAPI, Pydantic, SQLAlchemy 2 (síncrono), Alembic |
| Banco | PostgreSQL 16 |
| Autenticação | JWT, um único administrador |
| Infra | Docker, Docker Compose, Caddy (produção) |

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


As credenciais vêm do ambiente (`ADMIN_USERNAME` e `ADMIN_PASSWORD`) e nunca do
código. A senha é gravada com hash bcrypt — em texto puro ela não toca o banco,
o log nem o frontend.

```bash
docker compose exec backend python -m app.cli create-admin
```

O comando é idempotente: rodar de novo apenas atualiza a senha.

A senha **nunca** é passada como argumento (ficaria no histórico do shell e na
listagem de processos): ou vem de `ADMIN_PASSWORD`, ou é digitada sem eco.
Mínimo de 12 caracteres, e o limite de 72 **bytes** do bcrypt é conferido em
UTF-8 — `sãopaulo1234` tem 12 caracteres e 13 bytes.

> **Depois de criar o administrador, você pode remover `ADMIN_PASSWORD` do `.env`.**
> O hash já está no banco e nenhuma outra parte do sistema lê essa variável.
> Ela só volta a ser necessária se você quiser trocar a senha.

---

## Dados de desenvolvimento (seed)

```bash
docker compose exec backend python -m app.cli seed
```

Cria 10 jogadores e 6 partidas **fictícios**, cobrindo os três status. O comando
**recusa rodar se já houver partidas**, para não misturar exemplo com dado real.
O administrador é criado à parte, com `create-admin`. Nunca rode em produção.

---

## Testes

```bash
docker compose exec backend pytest -v      # backend
docker compose exec frontend npm run typecheck   # tipos do frontend
```

Cobrem integridade do banco, estatísticas derivadas e autenticação. Os testes
restantes de regra de negócio chegam na Fase 12.

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

Em **produção** o arquivo é outro: `.env.prod`, criado a partir do
`.env.prod.example`, também fora do Git. Ele traz as mesmas variáveis acima
(sem as `VITE_*`, que o frontend congela no build) mais estas:

| Variável | Para que serve |
|---|---|
| `APP_ENV` | `production` liga o fail-fast, fecha `/docs` e bloqueia o seed |
| `LOG_LEVEL` | Nível dos logs (`INFO` em produção) |
| `DOMINIO` | Domínio que o Caddy atende. `:80` valida sem domínio, sem TLS |
| `BACKUP_DIR` | Onde os backups são gravados na VPS antes de subir para o R2 |
| `BACKUP_RETENCAO_DIAS` | Dias que as cópias locais sobrevivem (padrão 30) |
| `RCLONE_REMOTE` / `RCLONE_BUCKET` | Remote e bucket do Cloudflare R2 |

`POSTGRES_PORT`, `VITE_API_URL` e `VITE_PROXY_TARGET` **não existem em produção**:
o Postgres não publica porta e o caminho da API é fixado em `/api` no build.

---

## Deploy em produção

Produção usa um arquivo próprio, `docker-compose.prod.yml`. O de desenvolvimento
continua exatamente como está.

**Diferenças que importam:** só o Caddy publica porta (80/443) — backend e Postgres
não publicam nenhuma; o React vai compilado, servido como arquivo estático, sem dev
server; o uvicorn roda com workers e sem `--reload`; e nada de bind mount de código,
que é o que torna o rollback confiável.

### Arquitetura

```
Internet → :80/:443 → Caddy ─┬─ /          arquivos estáticos (React)
                             ├─ /api/*     backend:8000
                             └─ /media/*   backend:8000
                                              ↓ rede interna
                                           PostgreSQL (sem porta pública)
```

Duas redes: `edge` (Caddy ↔ backend) e `interna` (backend ↔ banco, com
`internal: true`). O Caddy **não alcança o Postgres**.

### Primeira subida

```bash
# 1. Na VPS: Docker instalado, firewall liberando só 22, 80 e 443
sudo ufw allow 22 && sudo ufw allow 80 && sudo ufw allow 443 && sudo ufw enable

# 2. DNS: registro A do domínio → IP da VPS, e ESPERE propagar.
#    Subir antes disso faz o Let's Encrypt falhar, e tentativas repetidas
#    batem no limite semanal.

# 3. Código e configuração
git clone <repositório> /opt/futebol_quinta && cd /opt/futebol_quinta
cp .env.prod.example .env.prod
nano .env.prod          # preencha tudo; instruções estão no próprio arquivo
chmod 600 .env.prod

# 4. Suba
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build

# 5. Crie o administrador (uma única vez)
docker compose -f docker-compose.prod.yml --env-file .env.prod \
  exec backend python -m app.cli create-admin
#    Depois disso você pode remover ADMIN_PASSWORD do .env.prod:
#    o hash já está no banco.

# 6. Verifique
./scripts/smoke.sh https://seudominio.com.br

# 7. Instale o backup e RODE UM RESTORE DE TESTE agora, não depois
crontab -e   # 0 3 * * * cd /opt/futebol_quinta && ./scripts/backup.sh >> /var/log/migue-backup.log 2>&1
./scripts/backup.sh
./scripts/restore.sh /var/backups/migue/db-*.dump /var/backups/migue/media-*.tar.gz
```

**Sem domínio ainda?** Use `DOMINIO=:80` no `.env.prod`. O Caddy serve por HTTP sem
tentar certificado, e você valida a stack inteira — build estático, fallback de SPA,
proxy, migrations, admin, smoke tests. Quando o domínio existir, troque a variável e
suba de novo.

### A aplicação recusa iniciar se a configuração estiver insegura

Com `APP_ENV=production`, o backend **não sobe** se `SECRET_KEY`, `DATABASE_URL` ou
`CORS_ORIGINS` estiverem ausentes ou com valor de exemplo. É proposital: um site fora
do ar chama atenção na hora; um site no ar com a chave de exemplo do repositório, não.

Em produção `/docs`, `/redoc` e `/openapi.json` também ficam fechados, e o comando
`seed` recusa rodar.

### Atualização

```bash
./scripts/backup.sh                                    # o bilhete de volta vem primeiro
git pull
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
#   as migrations pendentes são aplicadas sozinhas pelo entrypoint
./scripts/smoke.sh https://seudominio.com.br
```

Alguns segundos de indisponibilidade enquanto o backend reinicia.

### Rollback

```bash
git checkout <sha-anterior>
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
```

Se a atualização incluía migration que apagou dado, o caminho é o dump feito antes:

```bash
./scripts/restore.sh <dump> <tar> --producao
```

**É por isso que o backup vem antes do deploy.** Rollback de código é trivial; de
migration destrutiva, não.

### Backup

Roda todo dia às 3h e envia para o **Cloudflare R2** via `rclone` — outro provedor,
outra conta. Volume Docker não é backup: ele morre junto com a VPS.

Salva **as duas coisas**: o banco (`pg_dump -Fc`) e as fotos (`tar` do volume). Um dump
do Postgres sozinho não bastaria — ele guarda os *caminhos* das fotos, não os arquivos.

```bash
rclone config          # uma vez: remote "r2" apontando para o bucket
./scripts/backup.sh    # manual, quando quiser
./scripts/restore.sh <dump> <tar>              # restaura em banco descartável e valida
./scripts/restore.sh <dump> <tar> --producao   # restaura de verdade; pede confirmação
```

O restore de teste confere tabelas, revisão do Alembic, contagens de jogadores,
partidas e participações, uma partida conhecida e se toda foto referenciada no banco
existe no arquivo. **Rode-o a cada trimestre** — backup nunca restaurado é suposição,
não garantia.

### Observabilidade

Logs com nível controlável por `LOG_LEVEL` e rotação no Docker (10 MB × 3 por
container). Para saber que caiu, aponte um monitor externo gratuito para
`https://seudominio/api/health` — externo de propósito, porque monitoramento no mesmo
host cai junto com ele. Esse endpoint consulta o banco de verdade, então ele acusa
Postgres fora do ar, não só processo morto.

---

## Estrutura

```
futebol_quinta/
├── docker-compose.yml       desenvolvimento: db + backend + frontend
├── docker-compose.prod.yml  produção: db + backend + Caddy
├── .env.example             modelo de configuração (versionado)
├── .env.prod.example        modelo de configuração de produção (versionado)
├── docs/design/             telas de referência do projeto
├── scripts/                 backup.sh, restore.sh, smoke.sh
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
    ├── Dockerfile.prod      build estático + Caddy
    ├── Caddyfile            HTTPS, proxy e fallback de SPA
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
| 3 | Models, migration do schema, repositories | ✅ |
| 4 | Autenticação | ✅ |
| 5 | Design system e layout | ✅ |
| 6 | Jogadores | ✅ |
| 7 | Partidas | ✅ |
| 8 | Dashboard e gráficos | ✅ |
| 9 | Rankings | ✅ |
| 10 | Histórico e detalhes da partida | ✅ |
| 11 | Preparação para produção e deploy | ✅ |
| 12 | Refino visual, responsividade e testes de frontend | — |
| 13 | Documentação final | — |
