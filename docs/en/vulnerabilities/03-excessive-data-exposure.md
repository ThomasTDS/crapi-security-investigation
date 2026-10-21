[🇧🇷 Português](../../vulnerabilidades/03-excessive-data-exposure.md) · 🇺🇸 English

# Excessive Data Exposure — Endpoint leaking other users' data

**OWASP API Security Top 10 (2023) category:** `API3 — Broken Object Property Level Authorization (Excessive Data Exposure)`
**Estimated severity:** `High`
**Matching crAPI challenge:** Challenge 4 — "find an endpoint that leaks sensitive information of other users"

---

## 1. Summary

An endpoint returns **more fields than the interface uses**. When listing public items (such as community/forum posts), the API includes sensitive author data in the JSON — email, phone number, `vehicleId`, etc. — that the screen never shows. The attacker reads this data directly from the response.

## 2. Preconditions

- Any authenticated account (community posts are visible to logged-in users).

## 3. Exploitation walkthrough

1. Authenticate and list the recent community posts:

```http
GET /community/api/v2/community/posts/recent HTTP/1.1
Host: localhost:8888
Authorization: Bearer <token>
```

2. Inspect the returned JSON. Beyond the post content, the response tends to include, for each author, an object with fields such as `email`, `vehicleid`, `profile_pic_url`, `nickname` — data the interface does not display.

3. These leaked fields feed other attacks: the `email` enables the [OTP brute-force](02-broken-authentication.md); the `vehicleid` enables the [location BOLA](01-bola-vehicle-location.md).

## 4. Evidence

**Confirmed against the local instance** — capture in [`evidencias/03-excessive-data-exposure/captura.txt`](../../../evidencias/03-excessive-data-exposure/captura.txt).

The response of `GET /community/api/v2/community/posts/recent` includes, for each author, an object with sensitive fields that the forum screen never shows:

```json
"author": {
  "nickname": "Adam",
  "email": "adam007@example.com",
  "vehicleid": "f89b5f21-7829-45cb-a650-299a61090378"
}
```

The `email` and `vehicleid` leaked here were used directly in the [BOLA](01-bola-vehicle-location.md) and [OTP brute-force](02-broken-authentication.md) attacks.

## 5. Why it is a risk

The server delegates to the client the responsibility of "not showing" sensitive data — but whoever consumes the API sees the entire JSON. This leaks PII (personal data) of every user and serves as a **springboard for other attacks** (the email and vehicle ID collected here are direct input for BOLA and account takeover). It is a common design mistake: serializing the whole database object instead of a lean DTO.

## 6. How to fix

- Return only the fields strictly needed for each response (**allow-list** / endpoint-specific DTOs), never the full database object.
- Never trust the client to filter sensitive data.
- Review list-endpoint responses, where the leak often goes unnoticed because it repeats across many records.

## 7. References

- [API3:2023 Broken Object Property Level Authorization](https://owasp.org/API-Security/editions/2023/en/0xa3-broken-object-property-level-authorization/)
