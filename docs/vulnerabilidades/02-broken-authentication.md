# Broken Authentication — Redefinição de senha via brute-force de OTP

**Categoria OWASP API Security Top 10 (2023):** `API2 — Broken Authentication`
**Severidade estimada:** `Crítica`
**Desafio crAPI correspondente:** Challenge 3 — "reset the password of a different user"

---

## 1. Resumo

O fluxo de redefinição de senha envia um **OTP numérico curto** por e-mail e expõe um endpoint de verificação (`check-otp`) **sem limite de tentativas** em determinadas versões. Como o OTP tem poucos dígitos, um atacante consegue testar todas as combinações (brute-force) e assumir a conta de outro usuário sem nunca ter acesso ao e-mail dele.

## 2. Pré-condições

- O **e-mail da vítima** (frequentemente vazado por [Excessive Data Exposure](03-excessive-data-exposure.md)).
- Nenhuma autenticação prévia é necessária — o fluxo de reset é público.

## 3. Passo a passo da exploração

1. Dispare o envio de OTP para o e-mail da vítima:

```http
POST /identity/api/auth/forget-password HTTP/1.1
Host: localhost:8888
Content-Type: application/json

{ "email": "vitima@exemplo.com" }
```

2. Tente validar o OTP forçando todas as combinações. O endpoint `v2` historicamente não limita tentativas; se o `v3` aplicar rate limit, testar o `v2` (APIs REST são previsíveis — versões antigas às vezes continuam expostas):

```http
POST /identity/api/auth/v3/check-otp HTTP/1.1
Host: localhost:8888
Content-Type: application/json

{ "email": "vitima@exemplo.com", "otp": "0000", "password": "NovaSenha123!" }
```

3. Itere `otp` de `0000` a `9999` (ou faixa correspondente ao tamanho do OTP) até receber sucesso. A resposta de sucesso confirma a troca de senha da vítima.

> **Automação:** no Postman, use o Collection Runner com um data file de OTPs, ou um runner/Newman. Importante: isso só é aceitável porque o alvo é local e proposital.

## 4. Evidência

**Confirmado contra a instância local** — captura em [`evidencias/02-broken-authentication/captura.txt`](../../evidencias/02-broken-authentication/captura.txt).

- **Sem rate limiting:** 30 tentativas seguidas com OTP errado no endpoint `v3/check-otp` retornaram **29×HTTP 500 (`Invalid OTP`) + 1×503** — nenhuma resposta `429`, nenhum bloqueio de conta. O OTP é de **4 dígitos** (apenas 10.000 combinações), então o brute-force é trivial.
- **Takeover efetivado:** com o OTP correto, a resposta foi `{"message":"OTP verified","status":200}` e o login com a **nova senha** definida pelo atacante retornou **HTTP 200** — ou seja, a conta da vítima foi assumida sem acesso ao e-mail dela.
- O endpoint `v2/check-otp` também existe e aceita tentativas, reforçando o problema de versões antigas mantidas no ar.

## 5. Por que é um risco

É **account takeover** completo: o atacante assume a conta sem credenciais e sem acesso ao e-mail da vítima. Dois erros se combinam — OTP curto (espaço de busca pequeno) e ausência de rate limiting — transformando um fator de segurança em uma porta destrancada. Manter uma versão antiga do endpoint sem proteção (`v2`) ao lado da nova (`v3`) é um agravante clássico.

## 6. Como corrigir

- Aplicar **rate limiting** e **bloqueio progressivo** por conta/IP no endpoint de verificação de OTP.
- Usar OTPs mais longos e com **expiração curta** e invalidação após N tentativas.
- **Desativar versões antigas** de endpoints que não tenham as mesmas proteções.
- Considerar fatores adicionais para ações sensíveis (reset de senha).

## 7. Referências

- [API2:2023 Broken Authentication](https://owasp.org/API-Security/editions/2023/en/0xa2-broken-authentication/)
