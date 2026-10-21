🇧🇷 Português · [🇺🇸 English](README.en.md)

# crAPI — Investigação de Segurança de API (OWASP API Security Top 10)

[![ZAP Baseline](https://github.com/ThomasTDS/crapi-security-investigation/actions/workflows/zap-baseline.yml/badge.svg)](https://github.com/ThomasTDS/crapi-security-investigation/actions/workflows/zap-baseline.yml)
[![OWASP API Security Top 10](https://img.shields.io/badge/OWASP-API%20Security%20Top%2010-000000)](https://owasp.org/API-Security/editions/2023/en/0x00-header/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

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
| 7 | **API2 — Broken Authentication (forja de JWT)** | Assinatura do JWT não verificada → virar admin / personificar usuários | [docs](docs/vulnerabilidades/07-jwt-forgery.md) |
| 8 | **Cadeia API3 + API7 → Shell Injection** | Mass Assignment + SSRF alcançam injeção de comando no backend | [docs](docs/vulnerabilidades/08-shell-injection.md) |

Cada documento segue o mesmo formato: classificação OWASP, pré-condições, passo a passo da requisição, evidência, impacto/risco e recomendação de correção. **As 8 vulnerabilidades foram reproduzidas e confirmadas** contra uma instância local do crAPI; as respostas reais estão em [evidencias/](evidencias/) e podem ser regeradas com [`scripts/capturar-evidencias.sh`](scripts/capturar-evidencias.sh) (as 6 primeiras) e [`scripts/capturar-extras.py`](scripts/capturar-extras.py) (JWT e shell injection). O item 8 é um bom exemplo de **encadeamento**: duas falhas de severidade média se combinam em um impacto crítico (RCE).

---

## Estrutura do repositório

```
.
├── docs/
│   ├── 00-ambiente-crapi.md          # como subir o crAPI localmente (Docker)
│   ├── template-vulnerabilidade.md   # modelo usado para documentar cada falha
│   └── vulnerabilidades/             # uma análise por vulnerabilidade
├── postman/
│   ├── crAPI-security.postman_collection.json     # requisições de cada ataque (catálogo)
│   ├── crAPI-evidencias.postman_collection.json   # coleção auto-suficiente p/ rodar no Newman
│   ├── crAPI.postman_environment.json             # variáveis de ambiente
│   └── amostra.mp4                                 # arquivo usado nos uploads de vídeo
├── scripts/
│   ├── capturar-evidencias.sh         # executa os 6 primeiros ataques e salva as respostas
│   ├── capturar-extras.py             # captura os extras (forja de JWT e shell injection)
│   └── gerar-relatorio-newman.sh      # gera o relatório HTML de evidências (Newman)
├── evidencias/                        # evidências das respostas (uma pasta por vulnerabilidade)
│   └── relatorio-newman.html          # relatório HTML navegável com todas as requisições
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

Para reproduzir todos os ataques de uma vez e regenerar as evidências:

```bash
BASE_URL=http://localhost:8888 \
EMAIL_VITIMA=vitima@teste.local SENHA_VITIMA='...' \
EMAIL_ATACANTE=atacante@teste.local SENHA_ATACANTE='...' \
bash scripts/capturar-evidencias.sh
```

### Relatório HTML (Newman)

Há também um relatório HTML navegável, com um print de cada requisição e sua resposta real, em [evidencias/relatorio-newman.html](evidencias/relatorio-newman.html) (baixe e abra no navegador). Ele é gerado rodando a coleção de evidências via Newman:

```bash
bash scripts/gerar-relatorio-newman.sh
```

O script mascara o token JWT real no HTML ao final, então o arquivo é seguro para versionar.

---

## Scan automatizado (OWASP ZAP em CI)

A pipeline [`.github/workflows/zap-baseline.yml`](.github/workflows/zap-baseline.yml) executa o **OWASP ZAP Baseline Scan** — um scan passivo que identifica cabeçalhos de segurança ausentes, cookies inseguros, divulgação de informação e outras configurações incorretas sem realizar ataques intrusivos.

Por rodar contra uma instância local do crAPI, o scan é disparado **manualmente** (`workflow_dispatch`) e opera sobre um ambiente efêmero subido pelo próprio workflow. O relatório é publicado como artifact da execução. Detalhes e ajuste de alertas em [.zap/rules.tsv](.zap/rules.tsv).

---

## Referências

- [OWASP crAPI](https://owasp.org/www-project-crapi/)
- [OWASP API Security Top 10 (2023)](https://owasp.org/API-Security/editions/2023/en/0x00-header/)
- [OWASP ZAP](https://www.zaproxy.org/)

---

## Licença

Distribuído sob a licença MIT. Veja [LICENSE](LICENSE).
