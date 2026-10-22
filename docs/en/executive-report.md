[🇧🇷 Português](../RELATORIO-EXECUTIVO.md) · 🇺🇸 English

# Executive report — crAPI security investigation

**Target:** crAPI (Completely Ridiculous API) — OWASP's intentionally vulnerable application, run **locally** via Docker.
**Scope:** crAPI's REST API (identity, community, and workshop services).
**Goal:** identify, safely exploit, and document flaws from the OWASP API Security Top 10.
**Date:** October 2026.

> Educational document. All tests were performed against a local, intentional instance. None of it should be applied to third-party systems without authorization.

---

## 1. Executive summary

**10 vulnerabilities were confirmed**, all reproduced against the local instance, with the request, real evidence, and remediation documented. The results show flaws in **authorization** (BOLA, BFLA), **authentication** (OTP brute-force, JWT forgery), **data exposure and manipulation** (excessive data exposure, mass assignment), **server requests** (SSRF), and **injection** (NoSQL, SQL) — plus a **chain** that leads to command execution (RCE).

Severity by **CVSS v3.1** band (base score):

| Severity | Count | Items |
|---|---|---|
| 🔴 Critical (9.0–10.0) | 2 | JWT forgery (9.8) · Broken Authentication/OTP (9.1) |
| 🟠 High (7.0–8.9) | 4 | SQL Injection (8.8) · SSRF (8.5) · Shell Injection (8.5) · BFLA (7.1) |
| 🟡 Medium (4.0–6.9) | 4 | BOLA (6.5) · Excessive Data Exposure (6.5) · Mass Assignment (6.5) · NoSQL Injection (5.4) |
| **Total** | **10** | |

**Highlight:** the **Shell Injection** item is not an isolated flaw — it is the chaining of **Mass Assignment + SSRF** to reach an internal command-injection point. Its CVSS is **8.5 (High)**: the impact is maximal (RCE, high C/I/A, changed scope), but the higher **attack complexity** (`AC:H`, since it requires the chain) keeps it below 9.0. It is the clearest example of how medium-severity flaws, combined, produce a severe impact.

---

## 2. Findings table

All 10 were **confirmed** against the local instance. Ordered by descending CVSS:

| # | Vulnerability | OWASP API Top 10 (2023) category | CVSS v3.1 | Severity | Detail |
|---|---|---|---|---|---|
| 7 | JWT forgery (signature not verified) | API2 — Broken Authentication | 9.8 | 🔴 Critical | [doc](vulnerabilities/07-jwt-forgery.md) |
| 2 | Broken Authentication — OTP brute-force | API2 — Broken Authentication | 9.1 | 🔴 Critical | [doc](vulnerabilities/02-broken-authentication.md) |
| 10 | SQL Injection — apply_coupon | Injection (was API8:2019) | 8.8 | 🟠 High | [doc](vulnerabilities/10-sql-injection.md) |
| 5 | SSRF | API7 — Server-Side Request Forgery | 8.5 | 🟠 High | [doc](vulnerabilities/05-ssrf.md) |
| 8 | Shell Injection (Mass Assignment + SSRF) | Chain API3 + API7 → command injection | 8.5 | 🟠 High | [doc](vulnerabilities/08-shell-injection.md) |
| 6 | BFLA — admin function by a regular user | API5 — Broken Function Level Authorization | 7.1 | 🟠 High | [doc](vulnerabilities/06-bfla.md) |
| 1 | BOLA — vehicle location | API1 — Broken Object Level Authorization | 6.5 | 🟡 Medium | [doc](vulnerabilities/01-bola-vehicle-location.md) |
| 3 | Excessive Data Exposure | API3 — Broken Object Property Level Authorization | 6.5 | 🟡 Medium | [doc](vulnerabilities/03-excessive-data-exposure.md) |
| 4 | Mass Assignment | API3 — Broken Object Property Level Authorization | 6.5 | 🟡 Medium | [doc](vulnerabilities/04-mass-assignment.md) |
| 9 | NoSQL Injection — coupon without code | Injection (was API8:2019) | 5.4 | 🟡 Medium | [doc](vulnerabilities/09-nosql-injection.md) |

---

## 3. Findings in detail (summary)

1. **BOLA — vehicle location** 🟡 — With their own token, the attacker reads another user's vehicle GPS location (ID obtained via item 3). No object-ownership check. → *physical tracking of any user.*
2. **Broken Authentication — OTP** 🔴 — `check-otp` has no rate limit and the OTP is 4 digits (10,000 combinations); brute-force leads to **account takeover** without access to the victim's email. → *account takeover.*
3. **Excessive Data Exposure** 🟡 — The community posts endpoint leaks every user's `email` and `vehicleid`. Feeds items 1 and 2. → *PII leak + springboard.*
4. **Mass Assignment** 🟡 — The client writes an order's `status` field and gets refunded without returning anything. → *financial fraud.*
5. **SSRF** 🟠 — `contact_mechanic` makes the server request an arbitrary URL; pointed at an internal service, it returned its content. → *internal network access.*
6. **BFLA** 🟠 — A regular user calls an admin endpoint and deletes another user's video. → *privileged operations by anyone.*
7. **JWT forgery** 🔴 — The server does not verify the signature (accepts `alg:none` and tampered payloads); allows becoming admin and impersonating any user. → *full authentication bypass.*
8. **Shell Injection (chain)** 🟠 — Mass Assignment writes a command into `conversion_params`; SSRF reaches the internal `convert_video`; the injection sink is hit. → *potential RCE.*
9. **NoSQL Injection** 🟡 — A MongoDB operator in `coupon_code` returns a valid coupon without knowing the code. → *fraud + query manipulation.*
10. **SQL Injection** 🟠 — `coupon_code` flows raw into SQL (error-based and boolean-based confirmed). → *read/alter database data.*

---

## 4. Recurring themes and priority recommendations

- **Server-side authorization, per object and per function** (items 1, 6): validate ownership/role in a central middleware, denying by default.
- **Never trust client input** (items 3, 4, 7, 9, 10): allow-list output and writable fields; type validation; parameterized queries; JWT signature verification with a fixed algorithm.
- **Control what the server accesses** (items 5, 8): allow-list request destinations; internal endpoints unreachable from user input.
- **Protect sensitive flows** (item 2): rate limiting, progressive lockout, longer OTP with expiry.
- **Defense in depth** (item 8): the biggest impact came from chaining — fix every link, not just the "most visible" flaw.

---

## 5. Automated scan (OWASP ZAP)

A **ZAP Baseline Scan** (passive) runs in CI against an ephemeral crAPI instance. Result: **0 High, 2 Medium** (missing CSP, missing anti-clickjacking), **7 Low** (CORS/X-Content-Type-Options headers, server version disclosure, timestamp) and 2 Informational. The passive scan complements — it does not replace — the manual authorization/business-logic tests above.

---

## 6. Conclusion

crAPI, as expected from a training target, concentrates representative flaws of the OWASP API Security Top 10. The investigation covered the most relevant classes and demonstrated, with reproducible evidence, everything from isolated authorization flaws to a **critical chain (RCE)**. The recommendations in section 4 address the root cause of most items: consistent server-side authorization, validation/parameterization of all input, and control over what the backend accesses.

**Artifacts:** per-vulnerability documentation in [vulnerabilities/](vulnerabilities/) · [diagrams](diagrams.md) (architecture + chaining) · real evidence in [../../evidencias/](../../evidencias/) · browsable HTML report in [../../evidencias/relatorio-newman.html](../../evidencias/relatorio-newman.html) · Postman collection and reproducible scripts in [../../postman/](../../postman/) and [../../scripts/](../../scripts/).
