# Deploy no Heroku

Este documento é o roteiro do Heroku. A seção **Deploy em produção** do
README continua descrevendo a stack de VPS da Fase 11 e **não foi alterada** —
ela é o caminho de volta enquanto o Heroku não estiver validado.

## Por que um app só

O React vai compilado dentro da mesma imagem que serve a API. Isso não é
economia de arquivo: é o que faz `VITE_API_URL=/api` e o `/media/<caminho>` do
`PlayerAvatar` continuarem valendo sem mudança nenhuma no frontend, e o que
mantém a conta dentro do crédito — dois dynos custariam o dobro e obrigariam a
configurar CORS de verdade.

```
Internet → roteador do Heroku (TLS) → dyno web
                                        ├─ /            React compilado (SPA fallback)
                                        ├─ /api/*       FastAPI
                                        └─ /media/*     302 → Cloudflare R2
                                              ↓
                                        Heroku Postgres (Essential-0)
```

## O que substituiu o quê

| Fase 11 (VPS) | Fase 12 (Heroku) |
|---|---|
| Caddy: TLS | roteador do Heroku |
| Caddy: headers, gzip, redirect HTTPS | `app/core/middleware.py` |
| Caddy: `try_files` | `SPAStaticFiles` |
| `docker-entrypoint.sh`: `alembic upgrade head` | release phase do `heroku.yml` |
| volume `media_data` | Cloudflare R2 (`R2Storage`) |
| `docker-compose.prod.yml` | `Dockerfile` da raiz + `heroku.yml` |
| `.env.prod` | `heroku config:set` |

## Primeira subida

```bash
# 1. Bucket das fotos, no Cloudflare R2
#    Painel do R2 → criar bucket "migue-fotos" (privado) e um API token
#    com permissão de leitura e escrita só nele. Anote o account id.

# 2. App no Heroku, no container stack
heroku login
heroku create migue-fc --stack container
heroku addons:create heroku-postgresql:essential-0 --app migue-fc
#    O addon injeta DATABASE_URL sozinho — e a reescreve quando rotaciona a
#    credencial. Não defina essa variável na mão.

# 3. Configuração
APP=migue-fc
heroku config:set --app $APP \
  APP_ENV=production \
  LOG_LEVEL=INFO \
  FORCE_HTTPS=true \
  TZ=America/Sao_Paulo \
  CURRENT_SEASON=2026 \
  SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')" \
  CORS_ORIGINS="https://$APP.herokuapp.com" \
  STORAGE_BACKEND=r2 \
  R2_ENDPOINT_URL="https://<id-da-conta>.r2.cloudflarestorage.com" \
  R2_ACCESS_KEY_ID="<chave>" \
  R2_SECRET_ACCESS_KEY="<segredo>" \
  R2_BUCKET=migue-fotos

# 4. Deploy. A release phase aplica as migrations sozinha, e se ela falhar o
#    release NÃO é promovido — a versão anterior continua no ar.
git push heroku main

# 5. Administrador (uma única vez)
heroku run --app $APP python -m app.cli create-admin
#    Ele pergunta a senha no terminal; ela não fica no histórico do shell.

# 6. Verifique
./scripts/heroku-smoke.sh https://$APP.herokuapp.com

# 7. Backup, e um restore de teste AGORA, não depois
export HEROKU_APP=$APP
./scripts/heroku-backup.sh
./scripts/heroku-restore.sh ~/backups/migue/db-*.dump
```

## Atualização

```bash
HEROKU_APP=migue-fc ./scripts/heroku-backup.sh   # o bilhete de volta vem primeiro
git push heroku main
./scripts/heroku-smoke.sh https://migue-fc.herokuapp.com
```

## Rollback

```bash
heroku releases --app migue-fc
heroku rollback v42 --app migue-fc
```

Rollback de release **não desfaz migration**. Se a versão nova incluía uma
migration destrutiva, o caminho é o dump feito antes — é por isso que o backup
vem primeiro.

## Coisas que mordem

- **`heroku config:unset ADMIN_PASSWORD`** se você chegou a defini-la como
  config var. O hash já está no banco e nada mais lê essa variável.
- **`WEB_CONCURRENCY`** é a alavanca de memória. O dyno Basic tem 512 MB; se
  aparecer `R14 (Memory quota exceeded)` nos logs, `heroku config:set
  WEB_CONCURRENCY=1`.
- **Conexões do banco.** `DB_POOL_SIZE` (3) e `DB_MAX_OVERFLOW` (2) por worker.
  O Essential-0 aceita ~20 no total. Antes de subir `WEB_CONCURRENCY`, refaça
  a conta.
- **`heroku pg:backups` tem retenção curta e mora no mesmo provedor.** É por
  isso que o `heroku-backup.sh` baixa o dump e manda para o R2.
