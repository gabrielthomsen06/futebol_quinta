#!/usr/bin/env bash
# Restore do SÓ NO MIGUÉ FC.
#
# Por padrão restaura num banco DESCARTÁVEL e valida o resultado — é o ensaio
# trimestral. Backup que nunca foi restaurado é suposição, não garantia, e o
# dia de descobrir que o dump estava vazio não pode ser o dia do desastre.
#
#   ./scripts/restore.sh db-2026-09-03-0300.dump media-2026-09-03-0300.tar.gz
#   ./scripts/restore.sh <dump> <tar> --producao   # restaura de verdade
#
# O modo --producao SOBRESCREVE o banco e as fotos. Ele pede confirmação.

set -euo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$RAIZ"

DUMP="${1:-}"
TAR="${2:-}"
MODO="${3:-teste}"
[ -n "$DUMP" ] && [ -n "$TAR" ] || {
  echo "Uso: $0 <db-*.dump> <media-*.tar.gz> [--producao]"; exit 1;
}
[ -f "$DUMP" ] || { echo "ERRO: $DUMP não encontrado."; exit 1; }
[ -f "$TAR" ]  || { echo "ERRO: $TAR não encontrado."; exit 1; }

ARQUIVO_ENV="${ARQUIVO_ENV:-.env.prod}"
# shellcheck disable=SC1090
set -a; . "./$ARQUIVO_ENV"; set +a
COMPOSE="docker compose -p ${COMPOSE_PROJETO:-migue-prod} -f docker-compose.prod.yml --env-file $ARQUIVO_ENV"

if [ "$MODO" = "--producao" ]; then
  ALVO="$POSTGRES_DB"
  echo "!! Isto vai SOBRESCREVER o banco '$ALVO' e as fotos de produção."
  read -r -p "!! Digite RESTAURAR para confirmar: " confirmacao
  [ "$confirmacao" = "RESTAURAR" ] || { echo "Cancelado."; exit 1; }
else
  ALVO="migue_restore_test"
  echo "==> Modo teste: restaurando em '$ALVO', sem tocar na produção."
fi

echo "==> [1/4] Preparando o banco de destino"
if [ "$MODO" != "--producao" ]; then
  $COMPOSE exec -T db psql -U "$POSTGRES_USER" -d postgres \
    -c "DROP DATABASE IF EXISTS $ALVO WITH (FORCE);" >/dev/null
  $COMPOSE exec -T db psql -U "$POSTGRES_USER" -d postgres \
    -c "CREATE DATABASE $ALVO;" >/dev/null
fi

echo "==> [2/4] Restaurando o banco"
$COMPOSE exec -T db pg_restore -U "$POSTGRES_USER" -d "$ALVO" --clean --if-exists < "$DUMP"

echo "==> [3/4] Restaurando as fotos"
if [ "$MODO" = "--producao" ]; then
  $COMPOSE exec -T backend sh -c 'rm -rf /app/media/* && mkdir -p /app/media'
  $COMPOSE exec -T backend tar xzf - -C /app/media < "$TAR"
  FOTOS=$($COMPOSE exec -T backend sh -c 'ls -1 /app/media/players 2>/dev/null | wc -l' | tr -d "\r")
else
  # No teste, só conferimos que o arquivo abre e quantas fotos tem.
  FOTOS=$(tar tzf "$TAR" | grep -c "players/" || true)
fi

echo "==> [4/4] Validando"
consultar() { $COMPOSE exec -T db psql -U "$POSTGRES_USER" -d "$ALVO" -tAc "$1" | tr -d "\r"; }

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
echo "    fotos no banco ..... $COM_FOTO"
echo "    fotos no arquivo ... $FOTOS"

FALHOU=0
[ "$TABELAS" = "5" ] || { echo "    FALHA: número de tabelas inesperado."; FALHOU=1; }
[ -n "$REVISAO" ]    || { echo "    FALHA: alembic_version vazia."; FALHOU=1; }
# O banco é a fonte da verdade: toda foto referenciada precisa existir no
# arquivo. O contrário (arquivo órfão) é inofensivo.
[ "$FOTOS" -ge "$COM_FOTO" ] || { echo "    FALHA: há fotos referenciadas que não estão no backup."; FALHOU=1; }

if [ "$MODO" != "--producao" ]; then
  echo "==> Descartando o banco de teste"
  $COMPOSE exec -T db psql -U "$POSTGRES_USER" -d postgres \
    -c "DROP DATABASE IF EXISTS $ALVO WITH (FORCE);" >/dev/null
fi

[ "$FALHOU" = "0" ] && echo "==> Restore validado." || { echo "==> RESTORE COM PROBLEMAS."; exit 1; }
