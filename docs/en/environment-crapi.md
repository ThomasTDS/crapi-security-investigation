[🇧🇷 Português](../00-ambiente-crapi.md) · 🇺🇸 English

# Environment — running crAPI locally

crAPI ships as a set of containers orchestrated by **Docker Compose**. This page describes how to bring the environment up and how to confirm it is ready for testing.

> All tests in this repository assume crAPI running **locally**. Never run the attacks described here against environments you do not control.

---

## 1. Prerequisites

- **Docker** (Engine 20.10+)
- **Docker Compose** (v2, bundled in modern Docker via `docker compose`)
- ~4 GB of free RAM for the containers
- Free ports: `8888` (web/API gateway) and `8025` (MailHog, to capture the emails/OTPs sent by the application)

Check the installation:

```bash
docker --version
docker compose version
```

---

## 2. Bringing the environment up

The official project provides a ready-made `docker-compose.yml`. The way OWASP recommends:

```bash
# download the latest official compose file
curl -o docker-compose.yml https://raw.githubusercontent.com/OWASP/crAPI/main/deploy/docker/docker-compose.yml

# start all services in the background
docker compose -f docker-compose.yml --compatibility up -d
```

The first run pulls several images and may take a few minutes.

> This `docker-compose.yml` is **not versioned** in this repository — it belongs to the crAPI project and is downloaded straight from the official source, ensuring you always use the current version and that this repo stays focused on the security investigation.

---

## 3. Confirming crAPI is up

- **Web UI:** open `http://localhost:8888`
- **Mailbox (MailHog):** open `http://localhost:8025` — this is where the verification emails and the **OTPs** used in the authentication tests arrive.

Quick command-line check:

```bash
curl -i http://localhost:8888/
```

---

## 4. Creating the test accounts

Several attacks (BOLA, Broken Authentication, BFLA) require **two accounts** — the "victim" and the "attacker" — to show that one user can access another user's data/functions.

1. In the web UI, register **user A (victim)** and, during sign-up, provide a vehicle number. crAPI sends an email with the vehicle code — grab it in MailHog (`http://localhost:8025`).
2. Register **user B (attacker)** the same way.
3. Log in with each account and keep the returned **JWT token** (see below) — it is used in authenticated requests.

### Getting the JWT token

```bash
curl -s -X POST http://localhost:8888/identity/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"YOUR_EMAIL","password":"YOUR_PASSWORD"}'
```

The response contains the `token` field. Use it in the `Authorization: Bearer <token>` header of the other requests.

---

## 5. Environment variables used in Postman

The collection in [../../postman/](../../postman/) depends on these variables (defined in the environment):

| Variable | Description | Example |
|---|---|---|
| `base_url` | crAPI base URL | `http://localhost:8888` |
| `token_vitima` | user A's JWT | `eyJhbGci...` |
| `token_atacante` | user B's JWT | `eyJhbGci...` |
| `email_vitima` | user A's email | `vitima@exemplo.com` |

---

## 6. Tearing the environment down

```bash
docker compose -f docker-compose.yml down

# to also remove the volumes (wipes the data)
docker compose -f docker-compose.yml down -v
```

---

## 7. Notes on endpoint versions

crAPI evolves: some endpoints exist in `v2` and `v3`, and exact paths may change between releases. The paths cited in each vulnerability's documentation were based on the project's known structure and **should be confirmed against your own instance** — the best source of truth is the real traffic captured in Postman/DevTools while using the app, plus the crAPI source code.
