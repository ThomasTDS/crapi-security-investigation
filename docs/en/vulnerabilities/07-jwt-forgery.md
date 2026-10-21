[🇧🇷 Português](../../vulnerabilidades/07-jwt-forgery.md) · 🇺🇸 English

# Broken Authentication — JWT forgery (signature not verified)

**OWASP API Security Top 10 (2023) category:** `API2 — Broken Authentication`
**Estimated severity:** `Critical`
**Matching crAPI challenge:** Challenge 15 — "forge valid JWTs"

---

## 1. Summary

crAPI tokens are issued with **RS256**, but the server **does not validate the signature** when receiving them. This allows forging arbitrary tokens: just build the desired payload and send it with `alg: none` (no signature) or with any signature. With this, an attacker **impersonates any user** (by changing `sub`) and **escalates privileges** (by changing `role` to `admin`), all without knowing any key.

## 2. Preconditions

- Any authenticated account (to obtain a legitimate reference token — optional, since the token can be built from scratch).

## 3. Exploitation walkthrough

A JWT has three parts: `header.payload.signature`. The legitimate header is `{"alg":"RS256"}` and the payload carries `sub`, `iat`, `exp`, and `role`.

1. **`alg: none`** — build a header `{"alg":"none","typ":"JWT"}`, a payload with the desired claims (e.g. `role: admin`) and **leave the signature empty**:

```
base64url({"alg":"none","typ":"JWT"}) + "." + base64url({...,"role":"admin"}) + "."
```

2. **Tampered payload + original signature** — reuse the header and signature of a legitimate token, changing only the payload. Since the signature is not checked, the token is accepted even though it does not match the content.

3. Send the forged token in `Authorization: Bearer <token>` to any authenticated endpoint.

The public JWKS key is exposed at `GET /.well-known/jwks.json` — but in this case it is not even needed, since the signature is not verified.

## 4. Evidence

**Confirmed against the local instance** — capture in [`evidencias/07-jwt-forgery/captura.txt`](../../../evidencias/07-jwt-forgery/captura.txt).

```
A) alg:none, role=admin (no signature)                   -> HTTP 200
B) tampered payload (role=admin) + original signature    -> HTTP 200
C) alg:none, sub=adam007@example.com                     -> HTTP 200
   {"id":1,"name":"Adam","email":"adam007@example.com","available_credit":100.0, ...}
```

Vector **C** is the most striking: an `alg:none` token with another user's `sub` returned **Adam's full dashboard** — total impersonation with no credential.

## 5. Why it is a risk

It is the worst possible flaw in token-based authentication: identity and privileges become **defined by the client**. An attacker becomes an administrator and takes over any user's account with a hand-built token. Accepting `alg: none` and not verifying the signature are classic JWT implementation/library mistakes.

## 6. How to fix

- **Verify the signature** of every received token against the correct public key.
- **Reject `alg: none`** and pin the expected algorithm (an `alg` allow-list), also avoiding RS256↔HS256 confusion.
- Validate `exp`/`iat` and, ideally, `iss`/`aud`.
- Use an up-to-date JWT library and configure it to fail safely (never accept a token without a valid signature).

## 7. References

- [API2:2023 Broken Authentication](https://owasp.org/API-Security/editions/2023/en/0xa2-broken-authentication/)
- [RFC 8725 — JSON Web Token Best Current Practices](https://datatracker.ietf.org/doc/html/rfc8725)
