[🇧🇷 Português](../../vulnerabilidades/02-broken-authentication.md) · 🇺🇸 English

# Broken Authentication — Password reset via OTP brute-force

**OWASP API Security Top 10 (2023) category:** `API2 — Broken Authentication`
**Estimated severity:** `Critical`
**Matching crAPI challenge:** Challenge 3 — "reset the password of a different user"

---

## 1. Summary

The password-reset flow sends a **short numeric OTP** by email and exposes a verification endpoint (`check-otp`) **with no attempt limit** in certain versions. Because the OTP has few digits, an attacker can try every combination (brute-force) and take over another user's account without ever having access to their email.

## 2. Preconditions

- The **victim's email** (often leaked via [Excessive Data Exposure](03-excessive-data-exposure.md)).
- No prior authentication is required — the reset flow is public.

## 3. Exploitation walkthrough

1. Trigger sending the OTP to the victim's email:

```http
POST /identity/api/auth/forget-password HTTP/1.1
Host: localhost:8888
Content-Type: application/json

{ "email": "vitima@exemplo.com" }
```

2. Try to validate the OTP by brute-forcing every combination. The `v2` endpoint historically does not limit attempts; if `v3` applies a rate limit, try `v2` (REST APIs are predictable — old versions are sometimes left exposed):

```http
POST /identity/api/auth/v3/check-otp HTTP/1.1
Host: localhost:8888
Content-Type: application/json

{ "email": "vitima@exemplo.com", "otp": "0000", "password": "NewPass123!" }
```

3. Iterate `otp` from `0000` to `9999` (or the range matching the OTP length) until you get success. The success response confirms the victim's password was changed.

> **Automation:** in Postman, use the Collection Runner with an OTP data file, or a runner/Newman. Note: this is only acceptable because the target is local and intentional.

## 4. Evidence

**Confirmed against the local instance** — capture in [`evidencias/02-broken-authentication/captura.txt`](../../../evidencias/02-broken-authentication/captura.txt).

- **No rate limiting:** 30 consecutive attempts with a wrong OTP on the `v3/check-otp` endpoint returned **29×HTTP 500 (`Invalid OTP`) + 1×503** — no `429` response, no account lockout. The OTP is **4 digits** (only 10,000 combinations), so the brute-force is trivial.
- **Takeover achieved:** with the correct OTP, the response was `{"message":"OTP verified","status":200}` and logging in with the **new password** set by the attacker returned **HTTP 200** — i.e., the victim's account was taken over without access to their email.
- The `v2/check-otp` endpoint also exists and accepts attempts, reinforcing the problem of old versions left online.

## 5. Why it is a risk

It is a full **account takeover**: the attacker takes over the account with no credentials and no access to the victim's email. Two mistakes combine — a short OTP (small search space) and the absence of rate limiting — turning a security factor into an unlocked door. Keeping an old, unprotected version of the endpoint (`v2`) alongside the new one (`v3`) is a classic aggravator.

## 6. How to fix

- Apply **rate limiting** and **progressive lockout** per account/IP on the OTP verification endpoint.
- Use longer OTPs with **short expiry** and invalidation after N attempts.
- **Disable old versions** of endpoints that lack the same protections.
- Consider additional factors for sensitive actions (password reset).

## 7. References

- [API2:2023 Broken Authentication](https://owasp.org/API-Security/editions/2023/en/0xa2-broken-authentication/)
