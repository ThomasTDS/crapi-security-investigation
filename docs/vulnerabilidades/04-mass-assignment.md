# Mass Assignment — Reembolso de um item nunca devolvido

**Categoria OWASP API Security Top 10 (2023):** `API3 — Broken Object Property Level Authorization (Mass Assignment)`
**Severidade estimada:** `Alta`
**Desafio crAPI correspondente:** Challenge 8 — "get an item for free" / Challenge 9 — "increase balance by $1,000+"

---

## 1. Resumo

Um endpoint de edição de pedido aceita no corpo da requisição **propriedades que não deveriam ser controladas pelo cliente** — como o status do pedido. Ao alterar o status de um pedido para "devolvido"/"reembolsado" sem ter devolvido nada, o atacante recebe o crédito de volta e fica com o item de graça.

## 2. Pré-condições

- Conta autenticada com pelo menos um **pedido** já realizado na loja do crAPI.
- O **ID do pedido** (obtido ao listar os próprios pedidos).

## 3. Passo a passo da exploração

1. Liste seus pedidos e pegue o `order_id` e o estado atual:

```http
GET /workshop/api/shop/orders HTTP/1.1
Host: localhost:8888
Authorization: Bearer <token>
```

2. Descubra o endpoint "sombra" que edita um pedido específico (estrutura REST previsível — ex.: `PUT`/`POST` sobre `/workshop/api/shop/orders/{order_id}`). Envie no corpo uma propriedade de controle que o cliente não deveria poder definir, como `status`:

```http
PUT /workshop/api/shop/orders/{order_id} HTTP/1.1
Host: localhost:8888
Authorization: Bearer <token>
Content-Type: application/json

{ "status": "returned", "quantity": 1 }
```

3. Se o saldo/crédito for devolvido sem qualquer validação de devolução física, o mass assignment está confirmado. Repetir para inflar o saldo (Challenge 9).

> **Confirmar na instância:** o nome exato do campo de status e o método/caminho do endpoint de edição devem ser validados observando o tráfego do fluxo legítimo de "return order".

## 4. Evidência

> _A preencher após execução._ Print salvo em `evidencias/04-mass-assignment/`. Mostrar o saldo/crédito **antes** e **depois** da requisição, provando o reembolso indevido, e o corpo da requisição com o campo injetado.

## 5. Por que é um risco

Tem **impacto financeiro direto**: o atacante obtém produtos sem pagar e pode inflar o próprio saldo arbitrariamente. A causa é vincular (bind) o corpo da requisição diretamente ao modelo do banco — campos internos como `status`, `balance` ou `role` acabam graváveis pelo cliente. É uma das falhas mais custosas quando atinge fluxos de pagamento.

## 6. Como corrigir

- Definir explicitamente **quais campos** podem ser escritos pelo cliente em cada endpoint (allow-list de propriedades / DTOs de entrada), ignorando o resto.
- Tratar mudanças de estado sensíveis (status de pedido, saldo) como **transições controladas pelo servidor**, nunca como atribuição livre vinda do payload.
- Testar cada endpoint de escrita injetando campos extras e verificar se são silenciosamente aceitos.

## 7. Referências

- [API3:2023 Broken Object Property Level Authorization](https://owasp.org/API-Security/editions/2023/en/0xa3-broken-object-property-level-authorization/)
