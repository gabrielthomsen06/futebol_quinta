#!/usr/bin/env bash
# Backup do SÓ NO MIGUÉ FC hospedado no Heroku.
#
# O scripts/backup.sh da Fase 11 continua no repositório e continua correto —
# para a VPS. Ele não serve aqui porque fazia `docker compose exec db pg_dump`
# e `tar` de um volume, e nenhuma das duas coisas existe no Heroku.
#
# O que mudou de verdade:
#   - o banco: o Heroku tem backup próprio (`pg:backups`), mas com retenção
#     curta e dentro do MESMO provedor. Este script baixa o dump e manda uma
#     cópia para fora — que era o objetivo do backup da Fase 11 e continua
#     sendo;
#   - as fotos: elas não são mais tarradas de um volume, já vivem no R2.
#     O espelho local abaixo é opcional e existe só para não deixá-las com
#     uma única cópia, num provedor só.
#
# Uso:  ./scripts/heroku-backup.sh
# Cron: 0 3 * * *  cd /caminho/do/repo && ./scripts/heroku-backup.sh >> /var/log/migue-backup.log 2>&1

set -euo pipefail

APP="${HEROKU_APP:?defina HEROKU_APP=<nome-do-app>}"
DESTINO="${BACKUP_DIR:-$HOME/backups/migue}"
RETENCAO="${BACKUP_RETENCAO_DIAS:-30}"
RCLONE_REMOTE="${RCLONE_REMOTE:-r2}"
RCLONE_BUCKET="${RCLONE_BUCKET:-migue-backups}"
R2_BUCKET_FOTOS="${R2_BUCKET:-migue-fotos}"
ESPELHAR_FOTOS="${ESPELHAR_FOTOS:-1}"
DATA="$(date +%F-%H%M)"

command -v heroku >/dev/null || { echo "ERRO: heroku CLI não encontrado."; exit 1; }
mkdir -p "$DESTINO"

echo "==> [1/4] Pedindo um backup novo ao Heroku"
heroku pg:backups:capture --app "$APP"

echo "==> [2/4] Baixando o dump"
ARQUIVO="$DESTINO/db-$DATA.dump"
heroku pg:backups:download --app "$APP" --output "$ARQUIVO"

# Um dump vazio é pior que nenhum: dá a sensação de estar protegido.
[ -s "$ARQUIVO" ] || { echo "ERRO: dump vazio."; exit 1; }
echo "    $(basename "$ARQUIVO") ($(du -h "$ARQUIVO" | cut -f1))"

echo "==> [3/4] Enviando o dump para fora do Heroku"
if command -v rclone >/dev/null 2>&1; then
  rclone copy "$ARQUIVO" "${RCLONE_REMOTE}:${RCLONE_BUCKET}/"
  echo "    enviado para ${RCLONE_REMOTE}:${RCLONE_BUCKET}/"

  if [ "$ESPELHAR_FOTOS" = "1" ]; then
    echo "    espelhando as fotos do R2 localmente"
    # As fotos JÁ estão no R2; isto só evita que exista uma cópia só.
    rclone sync "${RCLONE_REMOTE}:${R2_BUCKET_FOTOS}" "$DESTINO/fotos"
    echo "    $(find "$DESTINO/fotos" -type f 2>/dev/null | wc -l) foto(s) espelhada(s)"
  fi
else
  # Sem isto o backup do banco não sobrevive à perda da conta do Heroku,
  # que é o objetivo inteiro.
  echo "    AVISO: rclone não instalado — o dump ficou SÓ nesta máquina."
  echo "    Isso não é backup. Instale e configure o remote do R2."
fi

echo "==> [4/4] Limpando cópias locais com mais de $RETENCAO dias"
find "$DESTINO" -name "db-*.dump" -mtime +"$RETENCAO" -delete

date +%s > "$DESTINO/.ultimo-backup"
echo "==> Concluído: $DATA"
