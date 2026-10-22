🇧🇷 Português · [🇺🇸 English](en/diagrams.md)

# Diagramas — arquitetura e encadeamento de ataques

Dois diagramas que ajudam a visualizar **onde** cada falha vive e **como** elas se combinam. Renderizam automaticamente no GitHub (Mermaid).

---

## 1. Arquitetura do crAPI e mapa das falhas

O gateway (`crapi-web`, porta 8888) encaminha para três serviços, cada um com seu armazenamento. O diagrama mostra também em qual serviço cada vulnerabilidade foi encontrada.

```mermaid
flowchart LR
    ATK(["Atacante"]) -->|"JWT · :8888"| GW["crapi-web (gateway)"]
    GW --> ID["identity"]
    GW --> CO["community"]
    GW --> WS["workshop"]
    ID --> PG[("PostgreSQL")]
    WS --> PG
    CO --> MG[("MongoDB")]
    ID -. "OTP / e-mails" .-> MH["MailHog"]

    ID --- IDF["BOLA · Broken Auth (OTP) · JWT forgery · BFLA"]
    CO --- COF["Excessive Data Exposure · NoSQL injection"]
    WS --- WSF["Mass Assignment · SSRF · SQL injection · Shell injection"]
```

---

## 2. Encadeamento das vulnerabilidades

Poucas falhas são exploradas isoladamente: uma alimenta a outra. O **Excessive Data Exposure** entrega os insumos (e-mail, `vehicleid`) para o BOLA e o brute-force de OTP; e **Mass Assignment + SSRF** se combinam para alcançar a injeção de comando.

```mermaid
flowchart TD
    EDE["Excessive Data Exposure<br/>(posts da comunidade)"] -->|"e-mail"| OTP["Broken Auth: brute-force de OTP<br/>account takeover"]
    EDE -->|"vehicleid"| BOLA["BOLA<br/>localizacao do veiculo"]
    JWT["JWT forgery<br/>(assinatura nao verificada)"] --> IMP["Virar admin / personificar<br/>qualquer usuario"]
    MA["Mass Assignment<br/>(conversion_params)"] --> SINK["convert_video interno<br/>(ffmpeg)"]
    SSRF["SSRF<br/>(contact_mechanic)"] --> SINK
    SINK --> RCE["Shell Injection<br/>RCE potencial"]:::crit
    classDef crit fill:#fdd,stroke:#c00,stroke-width:2px
```

- **Caminho 1 (roubo de identidade/dados):** Excessive Data Exposure → OTP brute-force / BOLA.
- **Caminho 2 (bypass de autenticação):** JWT forgery → admin / personificação.
- **Caminho 3 (RCE):** Mass Assignment + SSRF → `convert_video` interno → Shell Injection.

Ver a análise completa de cada falha em [vulnerabilidades/](vulnerabilidades/) e o [relatório executivo](RELATORIO-EXECUTIVO.md).
