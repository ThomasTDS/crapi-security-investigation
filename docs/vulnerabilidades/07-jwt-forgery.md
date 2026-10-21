# Broken Authentication — Forja de JWT (assinatura não verificada)

**Categoria OWASP API Security Top 10 (2023):** `API2 — Broken Authentication`
**Severidade estimada:** `Crítica`
**Desafio crAPI correspondente:** Challenge 15 — "forge valid JWTs"

---

## 1. Resumo

Os tokens do crAPI são emitidos em **RS256**, mas o servidor **não valida a assinatura** ao recebê-los. Isso permite forjar tokens arbitrários: basta montar o payload desejado e enviá-lo com `alg: none` (sem assinatura) ou com uma assinatura qualquer. Com isso um atacante **personifica qualquer usuário** (trocando `sub`) e **escala privilégios** (trocando `role` para `admin`), tudo sem conhecer nenhuma chave.

## 2. Pré-condições

- Uma conta qualquer autenticada (para obter um token legítimo de referência — opcional, já que o token pode ser montado do zero).

## 3. Passo a passo da exploração

Um JWT tem três partes: `header.payload.signature`. O header legítimo é `{"alg":"RS256"}` e o payload traz `sub`, `iat`, `exp` e `role`.

1. **`alg: none`** — monte um header `{"alg":"none","typ":"JWT"}`, um payload com os claims desejados (ex.: `role: admin`) e **deixe a assinatura vazia**:

```
base64url({"alg":"none","typ":"JWT"}) + "." + base64url({...,"role":"admin"}) + "."
```

2. **Payload adulterado + assinatura original** — reaproveite o header e a assinatura de um token legítimo, trocando apenas o payload. Como a assinatura não é checada, o token é aceito mesmo não correspondendo ao conteúdo.

3. Envie o token forjado em `Authorization: Bearer <token>` para qualquer endpoint autenticado.

A chave JWKS pública fica exposta em `GET /.well-known/jwks.json` — mas, neste caso, nem é necessária, já que a assinatura não é verificada.

## 4. Evidência

**Confirmado contra a instância local** — captura em [`evidencias/07-jwt-forgery/captura.txt`](../../evidencias/07-jwt-forgery/captura.txt).

```
A) alg:none, role=admin (sem assinatura)                 -> HTTP 200
B) payload adulterado (role=admin) + assinatura original -> HTTP 200
C) alg:none, sub=adam007@example.com                     -> HTTP 200
   {"id":1,"name":"Adam","email":"adam007@example.com","available_credit":100.0, ...}
```

O vetor **C** é o mais contundente: um token `alg:none` com `sub` de outro usuário retornou o **dashboard completo do Adam** — personificação total sem credencial.

## 5. Por que é um risco

É a falha mais grave possível em autenticação baseada em token: a identidade e os privilégios passam a ser **definidos pelo cliente**. Um atacante vira administrador e assume a conta de qualquer usuário com um token montado à mão. Aceitar `alg: none` e não verificar a assinatura são erros clássicos de implementação/biblioteca de JWT.

## 6. Como corrigir

- **Verificar a assinatura** de todo token recebido contra a chave pública correta.
- **Rejeitar `alg: none`** e fixar o algoritmo esperado (allow-list de `alg`), evitando também confusão RS256↔HS256.
- Validar `exp`/`iat` e, idealmente, `iss`/`aud`.
- Usar uma biblioteca de JWT atualizada e configurá-la para falhar de forma segura (nunca aceitar token sem assinatura válida).

## 7. Referências

- [API2:2023 Broken Authentication](https://owasp.org/API-Security/editions/2023/en/0xa2-broken-authentication/)
- [RFC 8725 — JSON Web Token Best Current Practices](https://datatracker.ietf.org/doc/html/rfc8725)
