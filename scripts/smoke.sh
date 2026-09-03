#!/usr/bin/env bash
# Smoke tests pós-deploy do SÓ NO MIGUÉ FC.
#
# Roteiro curto que percorre o caminho inteiro: proxy, HTTPS, SPA, API
# pública, autenticação e portas fechadas. Roda em segundos.
#
#   ./scripts/smoke.sh https://seudominio.com.br
#   ./scripts/smoke.sh http://localhost          # validação sem domínio

set -uo pipefail

BASE="${1:-http://localhost}"
FALHAS=0
N=0

verificar() {
  local descricao="$1" esperado="$2" obtido="$3"
  N=$((N + 1))
  if [ "$obtido" = "$esperado" ]; then
    printf "  %2d. %-52s OK\n" "$N" "$descricao"
  else
    printf "  %2d. %-52s FALHOU (esperado %s, veio %s)\n" "$N" "$descricao" "$esperado" "$obtido"
    FALHAS=$((FALHAS + 1))
  fi
}

codigo() { curl -s -o /dev/null -w "%{http_code}" "$@"; }

echo "==> Smoke tests em $BASE"

# --- proxy e HTTPS -----------------------------------------------------------
if [ "${BASE#https://}" != "$BASE" ]; then
  DOMINIO="${BASE#https://}"
  verificar "HTTP redireciona para HTTPS" "308" "$(codigo -o /dev/null "http://$DOMINIO/")"
  curl -sI "$BASE/" >/dev/null 2>&1 && TLS=ok || TLS=falhou
  verificar "certificado TLS válido" "ok" "$TLS"
else
  echo "  (sem domínio: redirecionamento e TLS não se aplicam)"
fi

# --- frontend ----------------------------------------------------------------
verificar "GET / devolve o app" "200" "$(codigo "$BASE/")"
verificar "F5 em rota interna (/rankings)" "200" "$(codigo "$BASE/rankings")"
verificar "F5 em rota profunda (/jogadores/x)" "200" "$(codigo "$BASE/jogadores/x")"

CABECALHOS=$(curl -sI "$BASE/")
for h in "X-Content-Type-Options" "X-Frame-Options" "Referrer-Policy"; do
  echo "$CABECALHOS" | grep -qi "^$h:" && R=presente || R=ausente
  verificar "header $h" "presente" "$R"
done

# --- API pública -------------------------------------------------------------
SAUDE=$(curl -s "$BASE/api/health")
echo "$SAUDE" | grep -q '"database":"ok"' && R=ok || R=falhou
verificar "GET /api/health com banco acessível" "ok" "$R"

for rota in /api/players /api/matches /api/rankings /api/dashboard /api/seasons; do
  verificar "GET $rota sem token" "200" "$(codigo "$BASE$rota")"
done

# --- documentação fechada ----------------------------------------------------
verificar "/api/docs fechado em produção" "404" "$(codigo "$BASE/api/docs")"

# --- autenticação ------------------------------------------------------------
verificar "POST /api/players sem token" "401" \
  "$(codigo -X POST "$BASE/api/players" -H 'Content-Type: application/json' -d '{"nickname":"x"}')"
verificar "GET /api/auth/me sem token" "401" "$(codigo "$BASE/api/auth/me")"

# --- portas que precisam estar fechadas --------------------------------------
if [ "${BASE#https://}" != "$BASE" ]; then
  ALVO="${BASE#https://}"
  for porta in 5432 8000; do
    timeout 3 bash -c "</dev/tcp/$ALVO/$porta" 2>/dev/null && R=aberta || R=fechada
    verificar "porta $porta fechada de fora" "fechada" "$R"
  done
fi

echo
if [ "$FALHAS" = "0" ]; then
  echo "==> $N verificações, todas passaram."
else
  echo "==> $N verificações, $FALHAS falharam."
  exit 1
fi
