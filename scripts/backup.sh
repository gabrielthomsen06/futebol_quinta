#!/usr/bin/env bash
# Backup do SÓ NO MIGUÉ FC: banco + fotos, enviados para fora da VPS.
#
# Duas coisas precisam ser salvas, e um dump do Postgres cobre só uma:
# o banco guarda os CAMINHOS das fotos, mas os arquivos vivem no volume
# migue_media. Restaurar só o banco devolveria um sistema com referências
# apontando para arquivos que não existem.
#
# Uso:  ./scripts/backup.sh
# Cron: 0 3 * * *  cd /opt/futebol_quinta && ./scripts/backup.sh >> /var/log/migue-backup.log 2>&1

set -euo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$RAIZ"

ARQUIVO_ENV="${ARQUIVO_ENV:-.env.prod}"
[ -f "$ARQUIVO_ENV" ] || { echo "ERRO: $ARQUIVO_ENV não encontrado."; exit 1; }
# shellcheck disable=SC1090
set -a; . "./$ARQUIVO_ENV"; set +a

COMPOSE="docker compose -p ${COMPOSE_PROJETO:-migue-prod} -f docker-compose.prod.yml --env-file $ARQUIVO_ENV"
DESTINO="${BACKUP_DIR:-/var/backups/migue}"
RETENCAO="${BACKUP_RETENCAO_DIAS:-30}"
DATA="$(date +%F-%H%M)"

mkdir -p "$DESTINO"

echo "==> [1/4] Banco (pg_dump -Fc)"
# -Fc: formato custom, já comprimido e com restore seletivo.
$COMPOSE exec -T db pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc \
  > "$DESTINO/db-$DATA.dump"

echo "==> [2/4] Fotos"
# Feito de dentro do backend, que já tem o volume montado: assim o script
# não precisa saber o nome do volume, que muda com o nome do projeto.
$COMPOSE exec -T backend tar czf - -C /app/media . \
  > "$DESTINO/media-$DATA.tar.gz"

TAMANHO_DB=$(du -h "$DESTINO/db-$DATA.dump" | cut -f1)
TAMANHO_MEDIA=$(du -h "$DESTINO/media-$DATA.tar.gz" | cut -f1)
echo "    db-$DATA.dump ($TAMANHO_DB) · media-$DATA.tar.gz ($TAMANHO_MEDIA)"

# Um dump vazio é pior que nenhum: dá a sensação de estar protegido.
[ -s "$DESTINO/db-$DATA.dump" ] || { echo "ERRO: dump vazio."; exit 1; }

echo "==> [3/4] Enviando para o Cloudflare R2"
if command -v rclone >/dev/null 2>&1; then
  rclone copy "$DESTINO/db-$DATA.dump"       "${RCLONE_REMOTE}:${RCLONE_BUCKET}/"
  rclone copy "$DESTINO/media-$DATA.tar.gz"  "${RCLONE_REMOTE}:${RCLONE_BUCKET}/"
  echo "    enviado para ${RCLONE_REMOTE}:${RCLONE_BUCKET}/"
else
  # Sem isto o backup não sobrevive à perda da VPS, que é o objetivo inteiro.
  echo "    AVISO: rclone não instalado — os arquivos ficaram SÓ na VPS."
  echo "    Isso não é backup. Instale e configure o remote do R2."
fi

echo "==> [4/4] Limpando cópias locais com mais de $RETENCAO dias"
find "$DESTINO" -name "db-*.dump"      -mtime +"$RETENCAO" -delete
find "$DESTINO" -name "media-*.tar.gz" -mtime +"$RETENCAO" -delete

# Marca de sucesso, para a checagem semanal reclamar se ficar velha.
# Backup que falha em silêncio é pior que backup nenhum.
date +%s > "$DESTINO/.ultimo-backup"
echo "==> Concluído: $DATA"
