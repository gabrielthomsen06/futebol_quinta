#!/usr/bin/env bash
# Smoke tests pós-deploy no Heroku.
#
# Irmão do scripts/smoke.sh, que continua valendo para a stack da VPS. As
# diferenças não são cosméticas:
#   - somem as checagens de porta fechada: o Postgres do Heroku é alcançável
#     da internet por projeto, protegido por credencial e TLS, não por firewall;
#   - o teste de /docs passa a apontar para /docs. No smoke.sh ele mirava
#     /api/docs, um caminho que nunca existiu — o teste passava sempre, sem
#     testar nada. Aqui ele importa de verdade, porque com o React servido
#     pela própria API o /docs chega ao backend.
#
#   ./scripts/heroku-smoke.sh https://migue-fc-xxxx.herokuapp.com

set -uo pipefail

BASE="${1:-}"
[ -n "$BASE" ] || { echo "Uso: $0 https://<app>.herokuapp.com"; exit 1; }
BASE="${BASE%/}"
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

# --- TLS e redirecionamento --------------------------------------------------
DOMINIO="${BASE#https://}"
verificar "HTTP redireciona para HTTPS" "308" "$(codigo -o /dev/null "http://$DOMINIO/")"
curl -sI "$BASE/" >/dev/null 2>&1 && TLS=ok || TLS=falhou
verificar "certificado TLS válido" "ok" "$TLS"

# --- frontend servido pela própria API ---------------------------------------
verificar "GET / devolve o app" "200" "$(codigo "$BASE/")"
verificar "F5 em rota interna (/rankings)" "200" "$(codigo "$BASE/rankings")"
verificar "F5 em rota profunda (/jogadores/x)" "200" "$(codigo "$BASE/jogadores/x")"
# O fallback de SPA não pode engolir 404 de API: senão uma rota errada do
# backend devolveria a página do React e pareceria ter funcionado.
verificar "rota de API inexistente dá 404" "404" "$(codigo "$BASE/api/rota-que-nao-existe")"

CABECALHOS=$(curl -sI "$BASE/")
for h in "Strict-Transport-Security" "X-Content-Type-Options" "X-Frame-Options" "Referrer-Policy"; do
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
verificar "/docs fechado em produção" "404" "$(codigo "$BASE/docs")"
verificar "/openapi.json fechado em produção" "404" "$(codigo "$BASE/openapi.json")"

# --- autenticação ------------------------------------------------------------
verificar "POST /api/players sem token" "401" \
  "$(codigo -X POST "$BASE/api/players" -H 'Content-Type: application/json' --data-binary '{"nickname":"x"}')"
verificar "GET /api/auth/me sem token" "401" "$(codigo "$BASE/api/auth/me")"

# --- fotos -------------------------------------------------------------------
# Um jogador com foto prova o caminho inteiro: banco -> /media -> R2. Sem
# nenhuma foto cadastrada ainda, o teste é pulado em vez de mentir.
FOTO=$(curl -s "$BASE/api/players" \
  | grep -o '"photo_path":"[^"]*"' | head -1 | cut -d'"' -f4)
if [ -n "$FOTO" ]; then
  verificar "GET /media/<foto> redireciona para o R2" "302" "$(codigo "$BASE/media/$FOTO")"
  TIPO=$(curl -sL -o /dev/null -w "%{content_type}" "$BASE/media/$FOTO")
  verificar "foto chega como imagem" "image/webp" "${TIPO%%;*}"
else
  echo "      (nenhum jogador com foto ainda — teste de mídia pulado)"
fi

echo
if [ "$FALHAS" = "0" ]; then
  echo "==> $N verificações, todas passaram."
else
  echo "==> $N verificações, $FALHAS falharam."
  exit 1
fi
