[🇧🇷 Português](../poc-correcao-sqli.md) · 🇺🇸 English

# Fix PoC — SQL Injection (apply_coupon)

Proof that the [SQL Injection](vulnerabilities/10-sql-injection.md) vulnerability can be **fixed** — not just found. We applied the patch to the crAPI `workshop` service running locally and re-tested the attack: it worked before, it is neutralized after, and the legitimate functionality still works.

> crAPI is Apache-2.0. The patch ([`poc-correcao/apply-coupon-sqli.patch`](../../poc-correcao/apply-coupon-sqli.patch)) targets `services/workshop/crapi/shop/views.py` and is an educational remediation exercise.

---

## 1. Root cause

In `ApplyCouponView` (`services/workshop/crapi/shop/views.py`), the client-supplied `coupon_code` is **concatenated** straight into the SQL query:

```python
cursor.execute(
    "SELECT coupon_code from applied_coupon WHERE user_id = "
    + str(user.id)
    + " AND coupon_code = '"
    + coupon_request_body["coupon_code"]
    + "'"
)
```

Any quote or operator in `coupon_code` changes the query structure — classic SQL injection.

## 2. The fix

Replace the concatenation with a **parameterized query** (parameter binding). User input is treated as a **value**, never as a SQL fragment:

```python
cursor.execute(
    "SELECT coupon_code FROM applied_coupon "
    "WHERE user_id = %s AND coupon_code = %s",
    [user.id, coupon_request_body["coupon_code"]],
)
```

Full patch: [`poc-correcao/apply-coupon-sqli.patch`](../../poc-correcao/apply-coupon-sqli.patch).

## 3. How to reproduce (local environment)

With crAPI running (see [environment](environment-crapi.md)), apply the patch to the workshop container and restart it:

```bash
# 1) copy the file out of the container
docker cp crapi-workshop:/app/crapi/shop/views.py views.py

# 2) apply the patch (or edit manually per section 2)
patch views.py < poc-correcao/apply-coupon-sqli.patch

# 3) copy it back and restart the service
docker cp views.py crapi-workshop:/app/crapi/shop/views.py
docker restart crapi-workshop
```

> The patch also applies to a crAPI source checkout with `git apply poc-correcao/apply-coupon-sqli.patch` (followed by rebuilding the image).

## 4. Evidence (before / after)

Full capture in [`poc-correcao/evidencia-antes-depois.txt`](../../poc-correcao/evidencia-antes-depois.txt).

| Request | Before (vulnerable) | After (fixed) |
|---|---|---|
| `coupon_code: "TRAC075'"` | **HTTP 500** (broken query) | **400** `Coupon not found` |
| `coupon_code: "x' OR '1'='1"` | **400** citing `TRAC075` (injection) | **400** `Coupon not found` |
| `coupon_code: "TRAC075"` (legitimate) | applies / "already claimed" | **400** "already claimed" (functionality intact) |

The quote no longer breaks the query and `OR '1'='1'` no longer alters the `WHERE` — the injection is eliminated, with no regression in the legitimate flow.

## 5. Takeaway

The fix is simple and definitive: **never** build SQL by concatenating user input; always use bound parameters (prepared statements). The same principle applies to the project's other input points.
