#!/usr/bin/env bash
#
# Roda a coleção de evidências via Newman e gera o relatório HTML navegável
# (evidencias/relatorio-newman.html), com um print de cada requisição e sua
# resposta real. Ao final, mascara o token JWT real no HTML — então o arquivo
# gerado é seguro para versionar.
#
# Pré-requisitos: crAPI local no ar, Node/npm instalados, conta do atacante
# registrada (ver docs/00-ambiente-crapi.md).
#
# Uso:
#   bash scripts/gerar-relatorio-newman.sh
#
# As variáveis (base_url, credenciais) estão na própria coleção; para apontar
# para outro ambiente, edite postman/crAPI-evidencias.postman_collection.json
# ou passe --env-var na linha de comando do newman.

set -euo pipefail
cd "$(dirname "$0")/.."

OUT="evidencias/relatorio-newman.html"

npx --yes -p newman -p newman-reporter-htmlextra newman run \
  postman/crAPI-evidencias.postman_collection.json \
  --working-dir postman \
  -r cli,htmlextra \
  --reporter-htmlextra-export "$OUT" \
  --reporter-htmlextra-title "crAPI - Evidencias de Seguranca"

# Mascara o token JWT real (RS256) que aparece nos headers Authorization.
# Os tokens forjados (alg:none) são inofensivos e ficam visíveis de propósito.
sed -i -E 's/eyJhbGciOiJSUzI1NiJ9\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+/eyJhbGciOiJSUzI1NiJ9.TOKEN_REDACTED.TOKEN_REDACTED/g' "$OUT"

echo "Relatório gerado e token mascarado: $OUT"
