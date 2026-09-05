#!/usr/bin/env bash
# Restore do SÓ NO MIGUÉ FC hospedado no Heroku.
#
# Por padrão restaura num Postgres DESCARTÁVEL — o container `db` do
# docker-compose.yml de desenvolvimento — e valida o resultado. É o mesmo
# ensaio trimestral da Fase 11, pela mesma razão: backup que nunca foi
# restaurado é suposição, não garantia.
#
#   ./scripts/heroku-restore.sh ~/backups/migue/db-2026-09-04-0300.dump
#   ./scripts/heroku-restore.sh <url-publica-do-dump> --producao
#
# O modo --producao SOBRESCREVE o banco do app. Ele pede confirmação.

set -euo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$RAIZ"

DUMP="${1:-}"
MODO="${2:-teste}"
[ -n "$DUMP" ] || { echo "Uso: $0 <db-*.dump|url> [--producao]"; exit 1; }

if [ "$MODO" = "--producao" ]; then
  APP="${HEROKU_APP:?defina HEROKU_APP=<nome-do-app>}"
  echo "!! Isto vai SOBRESCREVER o banco de produção do app '$APP'."
  echo "!! As FOTOS não são tocadas: elas vivem no R2, não no Postgres. Se o"
  echo "!! dump for antigo, ele pode apontar para fotos que já foram trocadas."
  read -r -p "!! Digite RESTAURAR para confirmar: " confirmacao
  [ "$confirmacao" = "RESTAURAR" ] || { echo "Cancelado."; exit 1; }
  # O Heroku baixa o dump ele mesmo, então aqui a origem precisa ser uma URL.
  heroku pg:backups:restore "$DUMP" DATABASE_URL --app "$APP" --confirm "$APP"
  echo "==> Restaurado. Confira com ./scripts/heroku-smoke.sh https://<app>.herokuapp.com"
  exit 0
fi

[ -f "$DUMP" ] || { echo "ERRO: $DUMP não encontrado."; exit 1; }

ARQUIVO_ENV="${ARQUIVO_ENV:-.env}"
# shellcheck disable=SC1090
set -a; . "./$ARQUIVO_ENV"; set +a
ALVO="migue_restore_test"

echo "==> Modo teste: restaurando em '$ALVO' no Postgres de desenvolvimento."
docker compose up -d db >/dev/null

echo "==> [1/3] Preparando o banco de destino"
docker compose exec -T db psql -U "$POSTGRES_USER" -d postgres \
  -c "DROP DATABASE IF EXISTS $ALVO WITH (FORCE);" >/dev/null
docker compose exec -T db psql -U "$POSTGRES_USER" -d postgres \
  -c "CREATE DATABASE $ALVO;" >/dev/null

echo "==> [2/3] Restaurando"
docker compose exec -T db pg_restore -U "$POSTGRES_USER" -d "$ALVO" \
  --clean --if-exists --no-owner --no-acl < "$DUMP"

echo "==> [3/3] Validando"
consultar() { docker compose exec -T db psql -U "$POSTGRES_USER" -d "$ALVO" -tAc "$1" | tr -d "\r"; }

TABELAS=$(consultar "SELECT count(*) FROM pg_tables WHERE schemaname='public';")
REVISAO=$(consultar "SELECT version_num FROM alembic_version;")
JOGADORES=$(consultar "SELECT count(*) FROM players;")
PARTIDAS=$(consultar "SELECT count(*) FROM matches;")
PARTICIPACOES=$(consultar "SELECT count(*) FROM match_participations;")
COM_FOTO=$(consultar "SELECT count(*) FROM players WHERE photo_path IS NOT NULL;")
REALIZADAS=$(consultar "SELECT count(*) FROM matches WHERE status='PLAYED';")
GOLS=$(consultar "SELECT COALESCE(SUM(mp.goals),0) FROM match_participations mp JOIN matches m ON m.id=mp.match_id WHERE m.status='PLAYED';")

echo "    tabelas ............ $TABELAS   (esperado: 5)"
echo "    migration .......... $REVISAO"
echo "    jogadores .......... $JOGADORES"
echo "    partidas ........... $PARTIDAS  (realizadas: $REALIZADAS)"
echo "    participações ...... $PARTICIPACOES"
echo "    gols registrados ... $GOLS"
echo "    fotos referenciadas  $COM_FOTO  (os arquivos estão no R2)"

FALHOU=0
[ "$TABELAS" = "5" ] || { echo "    FALHA: número de tabelas inesperado."; FALHOU=1; }
[ -n "$REVISAO" ]    || { echo "    FALHA: alembic_version vazia."; FALHOU=1; }

# As fotos não vêm no dump. Conferir que as referenciadas existem no bucket é
# o equivalente ao que a Fase 11 fazia com o tar — e sem isso o restore
# validaria metade do sistema achando que validou tudo.
if [ "$COM_FOTO" != "0" ] && command -v rclone >/dev/null 2>&1; then
  NO_BUCKET=$(rclone ls "${RCLONE_REMOTE:-r2}:${R2_BUCKET:-migue-fotos}" 2>/dev/null | wc -l)
  echo "    fotos no bucket .... $NO_BUCKET"
  [ "$NO_BUCKET" -ge "$COM_FOTO" ] || { echo "    FALHA: há fotos referenciadas que não estão no R2."; FALHOU=1; }
fi

echo "==> Descartando o banco de teste"
docker compose exec -T db psql -U "$POSTGRES_USER" -d postgres \
  -c "DROP DATABASE IF EXISTS $ALVO WITH (FORCE);" >/dev/null

[ "$FALHOU" = "0" ] && echo "==> Restore validado." || { echo "==> RESTORE COM PROBLEMAS."; exit 1; }
