#!/bin/sh
set -e

echo "==> Aplicando migrations (alembic upgrade head)"
alembic upgrade head

echo "==> Iniciando a API"
exec "$@"
