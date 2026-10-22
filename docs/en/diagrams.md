[🇧🇷 Português](../diagramas.md) · 🇺🇸 English

# Diagrams — architecture and attack chaining

Two diagrams that help visualize **where** each flaw lives and **how** they combine. They render automatically on GitHub (Mermaid).

---

## 1. crAPI architecture and flaw map

The gateway (`crapi-web`, port 8888) forwards to three services, each with its own storage. The diagram also shows which service each vulnerability was found in.

```mermaid
flowchart LR
    ATK(["Attacker"]) -->|"JWT · :8888"| GW["crapi-web (gateway)"]
    GW --> ID["identity"]
    GW --> CO["community"]
    GW --> WS["workshop"]
    ID --> PG[("PostgreSQL")]
    WS --> PG
    CO --> MG[("MongoDB")]
    ID -. "OTP / emails" .-> MH["MailHog"]

    ID --- IDF["BOLA · Broken Auth (OTP) · JWT forgery · BFLA"]
    CO --- COF["Excessive Data Exposure · NoSQL injection"]
    WS --- WSF["Mass Assignment · SSRF · SQL injection · Shell injection"]
```

---

## 2. Vulnerability chaining

Few flaws are exploited in isolation: one feeds the next. **Excessive Data Exposure** supplies the inputs (email, `vehicleid`) for BOLA and the OTP brute-force; and **Mass Assignment + SSRF** combine to reach command injection.

```mermaid
flowchart TD
    EDE["Excessive Data Exposure<br/>(community posts)"] -->|"email"| OTP["Broken Auth: OTP brute-force<br/>account takeover"]
    EDE -->|"vehicleid"| BOLA["BOLA<br/>vehicle location"]
    JWT["JWT forgery<br/>(signature not verified)"] --> IMP["Become admin / impersonate<br/>any user"]
    MA["Mass Assignment<br/>(conversion_params)"] --> SINK["internal convert_video<br/>(ffmpeg)"]
    SSRF["SSRF<br/>(contact_mechanic)"] --> SINK
    SINK --> RCE["Shell Injection<br/>potential RCE"]:::crit
    classDef crit fill:#fdd,stroke:#c00,stroke-width:2px
```

- **Path 1 (identity/data theft):** Excessive Data Exposure → OTP brute-force / BOLA.
- **Path 2 (authentication bypass):** JWT forgery → admin / impersonation.
- **Path 3 (RCE):** Mass Assignment + SSRF → internal `convert_video` → Shell Injection.

See the full analysis of each flaw in [vulnerabilities/](vulnerabilities/) and the [executive report](executive-report.md).
