[🇧🇷 Português](README.md) · 🇺🇸 English

# crAPI — API Security Investigation (OWASP API Security Top 10)

[![ZAP Baseline](https://github.com/ThomasTDS/crapi-security-investigation/actions/workflows/zap-baseline.yml/badge.svg)](https://github.com/ThomasTDS/crapi-security-investigation/actions/workflows/zap-baseline.yml)
[![OWASP API Security Top 10](https://img.shields.io/badge/OWASP-API%20Security%20Top%2010-000000)](https://owasp.org/API-Security/editions/2023/en/0x00-header/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An **API security testing** project against [crAPI (Completely Ridiculous API)](https://owasp.org/www-project-crapi/), an intentionally vulnerable application maintained by OWASP and built specifically to practice identifying flaws from the **OWASP API Security Top 10**.

The goal is to demonstrate, end to end, the process of finding, safely exploiting, and **documenting** real API vulnerabilities: the request that exposes the problem, the evidence of exploitation, and an explanation of the business risk — plus an automated security scan (OWASP ZAP) wired into a CI pipeline.

> ⚠️ **Disclaimer.** Everything in this repository is educational and was produced against a **deliberately vulnerable application running locally**. None of it should be used against third-party systems without explicit authorization.

---

> 📋 **[Consolidated executive report](docs/en/executive-report.md)** — summary of the 10 findings with severity, recurring themes, and priority recommendations.
> 🗺️ **[Diagrams](docs/en/diagrams.md)** — crAPI architecture and vulnerability chaining.

## Covered vulnerabilities

| # | Category (OWASP API Security Top 10 — 2023) | crAPI scenario | Docs |
|---|---|---|---|
| 1 | **API1 — Broken Object Level Authorization (BOLA)** | Access another user's vehicle location | [docs](docs/en/vulnerabilities/01-bola-vehicle-location.md) |
| 2 | **API2 — Broken Authentication** | Reset another user's password via OTP brute-force | [docs](docs/en/vulnerabilities/02-broken-authentication.md) |
| 3 | **API3 — Excessive Data Exposure** | Endpoint leaking other users' sensitive data | [docs](docs/en/vulnerabilities/03-excessive-data-exposure.md) |
| 4 | **API3 — Mass Assignment** | Get refunded for an item never returned | [docs](docs/en/vulnerabilities/04-mass-assignment.md) |
| 5 | **API7 — Server-Side Request Forgery (SSRF)** | Force the server to call an arbitrary destination | [docs](docs/en/vulnerabilities/05-ssrf.md) |
| 6 | **API5 — Broken Function Level Authorization (BFLA)** | Regular user reaching an admin function | [docs](docs/en/vulnerabilities/06-bfla.md) |
| 7 | **API2 — Broken Authentication (JWT forgery)** | JWT signature not verified → become admin / impersonate users | [docs](docs/en/vulnerabilities/07-jwt-forgery.md) |
| 8 | **Chain API3 + API7 → Shell Injection** | Mass Assignment + SSRF reach command injection on the backend | [docs](docs/en/vulnerabilities/08-shell-injection.md) |
| 9 | **Injection — NoSQL Injection** | Get a valid coupon without knowing the code (MongoDB operator) | [docs](docs/en/vulnerabilities/09-nosql-injection.md) |
| 10 | **Injection — SQL Injection** | `coupon_code` concatenated into a SQL query without sanitization | [docs](docs/en/vulnerabilities/10-sql-injection.md) |

Each document follows the same format: OWASP classification, preconditions, step-by-step request, evidence, impact/risk, and remediation. **All 10 vulnerabilities were reproduced and confirmed** against a local crAPI instance; the real responses live in [evidencias/](evidencias/) and can be regenerated with [`scripts/capturar-evidencias.sh`](scripts/capturar-evidencias.sh) (the first 6), [`scripts/capturar-extras.py`](scripts/capturar-extras.py) (JWT and shell injection), and [`scripts/capturar-cupons.py`](scripts/capturar-cupons.py) (NoSQL/SQL injection). Item 8 is a good example of **chaining**: two medium-severity flaws combine into a critical impact (RCE).

> English documentation lives in [docs/en/](docs/en/); the Portuguese originals are under [docs/](docs/).

---

## Repository layout

```
.
├── docs/                             # Portuguese documentation
│   ├── 00-ambiente-crapi.md          # how to run crAPI locally (Docker)
│   ├── template-vulnerabilidade.md   # template used to document each flaw
│   ├── vulnerabilidades/             # one analysis per vulnerability (PT)
│   └── en/                           # English documentation (mirror)
├── postman/
│   ├── crAPI-security.postman_collection.json     # request for each attack (catalog)
│   ├── crAPI-evidencias.postman_collection.json   # self-contained collection to run in Newman
│   ├── crAPI.postman_environment.json             # environment variables
│   └── amostra.mp4                                 # file used in video uploads
├── scripts/
│   ├── capturar-evidencias.sh         # runs the first 6 attacks and saves the responses
│   ├── capturar-extras.py             # captures the extras (JWT forgery and shell injection)
│   ├── capturar-cupons.py             # captures the coupon injections (NoSQL/SQL)
│   └── gerar-relatorio-newman.sh      # generates the HTML evidence report (Newman)
├── evidencias/                        # response evidence (one folder per vulnerability)
│   └── relatorio-newman.html          # browsable HTML report with every request
├── .zap/
│   └── rules.tsv                     # OWASP ZAP alert tuning
└── .github/workflows/
    └── zap-baseline.yml              # security scan (ZAP baseline) in CI
```

---

## Prerequisites

- **Docker** and **Docker Compose** (to run crAPI locally)
- **Postman** (or Newman, to run the collection from the command line)

Full environment instructions in [docs/en/environment-crapi.md](docs/en/environment-crapi.md).

---

## How to use

1. Bring crAPI up locally following [docs/en/environment-crapi.md](docs/en/environment-crapi.md).
2. Import the collection and the environment from [postman/](postman/) into Postman.
3. Set the environment's `base_url` variable to your crAPI address (defaults to `http://localhost:8888`).
4. Follow each document in [docs/en/vulnerabilities/](docs/en/vulnerabilities/) to reproduce and understand each flaw.

To reproduce all attacks at once and regenerate the evidence:

```bash
BASE_URL=http://localhost:8888 \
EMAIL_VITIMA=vitima@teste.local SENHA_VITIMA='...' \
EMAIL_ATACANTE=atacante@teste.local SENHA_ATACANTE='...' \
bash scripts/capturar-evidencias.sh
```

### HTML report (Newman)

There is also a browsable HTML report, with a snapshot of each request and its real response, at [evidencias/relatorio-newman.html](evidencias/relatorio-newman.html) (download and open it in a browser). It is generated by running the evidence collection via Newman:

```bash
bash scripts/gerar-relatorio-newman.sh
```

The script masks the real JWT token in the HTML at the end, so the file is safe to version.

---

## Automated scan (OWASP ZAP in CI)

The [`.github/workflows/zap-baseline.yml`](.github/workflows/zap-baseline.yml) pipeline runs the **OWASP ZAP Baseline Scan** — a passive scan that flags missing security headers, insecure cookies, information disclosure, and other misconfigurations without performing intrusive attacks.

Because it runs against a local crAPI instance, the scan is triggered **manually** (`workflow_dispatch`) and operates on an ephemeral environment brought up by the workflow itself. The report is published as a run artifact. Details and alert tuning in [.zap/rules.tsv](.zap/rules.tsv).

---

## References

- [OWASP crAPI](https://owasp.org/www-project-crapi/)
- [OWASP API Security Top 10 (2023)](https://owasp.org/API-Security/editions/2023/en/0x00-header/)
- [OWASP ZAP](https://www.zaproxy.org/)

---

## License

Distributed under the MIT License. See [LICENSE](LICENSE).
