🇧🇷 Português · [🇺🇸 English](../en/vulnerabilities/11-unauth-access.md)

# Acesso não autenticado — endpoints de relatório sem checagem de token

**Categoria OWASP API Security Top 10 (2023):** `API2 — Broken Authentication`
**Severidade (CVSS v3.1):** `Média · 6.5` — `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:L/A:N`
**Desafio crAPI correspondente:** Challenge 14 — "find an endpoint that skips authentication checks"

---

## 1. Resumo

Alguns endpoints do serviço `workshop` (ligados ao relatório do mecânico) **não aplicam a verificação de token JWT** — no código, falta o decorator `@jwt_auth_required`. Qualquer pessoa, sem autenticação, consegue acioná-los: criar uma solicitação de serviço (`receive_report`) e acessar o endpoint de download de relatório (`download_report`), que inclusive vaza o caminho absoluto do servidor.

## 2. Pré-condições

- Nenhuma. Os endpoints respondem **sem token**.

## 3. Passo a passo da exploração

1. Chame `receive_report` **sem** header `Authorization`:

```http
GET /workshop/api/mechanic/receive_report?mechanic_code=TRAC_JHN&problem_details=teste&vin=<VIN> HTTP/1.1
Host: localhost:8888
```

2. Chame `download_report` **sem** token:

```http
GET /workshop/api/mechanic/download_report?filename=teste HTTP/1.1
Host: localhost:8888
```

3. Compare com um endpoint corretamente protegido (ex.: `GET /workshop/api/shop/products`), que **sem** token retorna `401`.

## 4. Evidência

**Confirmado contra a instância local** — captura em [`evidencias/11-unauth-access/captura.txt`](../../evidencias/11-unauth-access/captura.txt).

```
receive_report  (sem token) -> HTTP 500  (processa, NÃO retorna 401; criaria um service request com VIN válido)
download_report (sem token) -> HTTP 404  {"message":"File not found at '/app/reports/teste'."}
# contraste (endpoint protegido):
GET /workshop/api/shop/products (sem token) -> HTTP 401  {"message":"JWT Token required!"}
```

Enquanto o endpoint protegido devolve `401`, os endpoints de relatório **executam a lógica sem exigir autenticação**. O `download_report` ainda revela o caminho interno `/app/reports` — e é o ponto de entrada do [Path Traversal](12-path-traversal.md).

## 5. Por que é um risco

Endpoints sem autenticação permitem que qualquer um crie dados (poluição/abuso) e acesse funções que deveriam ser restritas — além de vazarem informações úteis a outros ataques (aqui, o caminho do sistema de arquivos, que habilita o Path Traversal). É um erro comum: esquecer o controle de autenticação em uma rota ao adicioná-la.

## 6. Como corrigir

- Exigir autenticação **por padrão** (deny-by-default) e aplicar o controle em todas as rotas que manipulam dados.
- Centralizar a verificação (middleware/decorator global), em vez de depender de lembrar o decorator em cada view.
- Revisar rotas recém-adicionadas especificamente quanto à presença do controle de auth.

## 7. Referências

- [API2:2023 Broken Authentication](https://owasp.org/API-Security/editions/2023/en/0xa2-broken-authentication/)
