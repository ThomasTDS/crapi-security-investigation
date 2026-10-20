# crAPI — Investigação de Segurança de API (OWASP API Security Top 10)

Projeto de **testes de segurança de API** sobre o [crAPI (Completely Ridiculous API)](https://owasp.org/www-project-crapi/), uma aplicação intencionalmente vulnerável mantida pela OWASP e criada justamente para treinar a identificação de falhas do **OWASP API Security Top 10**.

O objetivo é demonstrar, de ponta a ponta, o processo de encontrar, explorar de forma controlada e **documentar** vulnerabilidades reais de API: a requisição que expõe o problema, a evidência da exploração e a explicação do risco de negócio — além de um scan automatizado de segurança (OWASP ZAP) integrado a uma pipeline de CI.

> ⚠️ **Aviso.** Todo o conteúdo deste repositório é educacional e foi produzido contra uma aplicação **propositalmente vulnerável, rodando localmente**. Nada aqui deve ser aplicado contra sistemas de terceiros sem autorização expressa.

---

## Vulnerabilidades cobertas

| # | Categoria (OWASP API Security Top 10 — 2023) | Cenário no crAPI | Documentação |
|---|---|---|---|
| 1 | **API1 — Broken Object Level Authorization (BOLA)** | Acessar a localização do veículo de outro usuário | [docs](docs/vulnerabilidades/01-bola-localizacao-veiculo.md) |
| 2 | **API2 — Broken Authentication** | Redefinir a senha de outro usuário via brute-force de OTP | [docs](docs/vulnerabilidades/02-broken-authentication.md) |
| 3 | **API3 — Excessive Data Exposure** | Endpoint que vaza dados sensíveis de outros usuários | [docs](docs/vulnerabilidades/03-excessive-data-exposure.md) |
| 4 | **API3 — Mass Assignment** | Obter reembolso de um item nunca devolvido | [docs](docs/vulnerabilidades/04-mass-assignment.md) |
| 5 | **API7 — Server-Side Request Forgery (SSRF)** | Forçar o servidor a fazer requisições a um destino arbitrário | [docs](docs/vulnerabilidades/05-ssrf.md) |
| 6 | **API5 — Broken Function Level Authorization (BFLA)** | Usuário comum acessando função administrativa | [docs](docs/vulnerabilidades/06-bfla.md) |

Cada documento segue o mesmo formato: classificação OWASP, pré-condições, passo a passo da requisição, evidência, impacto/risco e recomendação de correção.

---

## Estrutura do repositório

```
.
├── docs/
│   ├── 00-ambiente-crapi.md          # como subir o crAPI localmente (Docker)
│   ├── template-vulnerabilidade.md   # modelo usado para documentar cada falha
│   └── vulnerabilidades/             # uma análise por vulnerabilidade
├── postman/
│   ├── crAPI-security.postman_collection.json   # requisições de cada ataque
│   └── crAPI.postman_environment.json           # variáveis de ambiente
├── evidencias/                       # prints das respostas (uma pasta por vulnerabilidade)
├── .zap/
│   └── rules.tsv                     # ajuste fino de alertas do OWASP ZAP
└── .github/workflows/
    └── zap-baseline.yml              # scan de segurança (ZAP baseline) em CI
```

---

## Pré-requisitos

- **Docker** e **Docker Compose** (para subir o crAPI localmente)
- **Postman** (ou Newman, para rodar a coleção via linha de comando)

Instruções completas de ambiente em [docs/00-ambiente-crapi.md](docs/00-ambiente-crapi.md).

---

## Como usar

1. Suba o crAPI localmente seguindo [docs/00-ambiente-crapi.md](docs/00-ambiente-crapi.md).
2. Importe a coleção e o environment da pasta [postman/](postman/) no Postman.
3. Ajuste a variável `base_url` do environment para o endereço do seu crAPI (por padrão `http://localhost:8888`).
4. Siga cada documento em [docs/vulnerabilidades/](docs/vulnerabilidades/) para reproduzir e entender cada falha.

---

## Scan automatizado (OWASP ZAP em CI)

A pipeline [`.github/workflows/zap-baseline.yml`](.github/workflows/zap-baseline.yml) executa o **OWASP ZAP Baseline Scan** — um scan passivo que identifica cabeçalhos de segurança ausentes, cookies inseguros, divulgação de informação e outras configurações incorretas sem realizar ataques intrusivos.

Por rodar contra uma instância local do crAPI, o scan é disparado **manualmente** (`workflow_dispatch`) e opera sobre um ambiente efêmero subido pelo próprio workflow. O relatório é publicado como artifact da execução. Detalhes e ajuste de alertas em [.zap/rules.tsv](.zap/rules.tsv).

---

## Referências

- [OWASP crAPI](https://owasp.org/www-project-crapi/)
- [OWASP API Security Top 10 (2023)](https://owasp.org/API-Security/editions/2023/en/0x00-header/)
- [OWASP ZAP](https://www.zaproxy.org/)
