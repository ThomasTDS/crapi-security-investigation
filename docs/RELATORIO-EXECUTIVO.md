🇧🇷 Português · [🇺🇸 English](en/executive-report.md)

# Relatório executivo — Investigação de segurança do crAPI

**Alvo:** crAPI (Completely Ridiculous API) — aplicação intencionalmente vulnerável da OWASP, executada **localmente** via Docker.
**Escopo:** API REST do crAPI (serviços de identidade, comunidade e workshop).
**Objetivo:** identificar, explorar de forma controlada e documentar falhas do OWASP API Security Top 10.
**Data:** outubro/2026.

> Documento educacional. Todos os testes foram feitos contra uma instância local e proposital. Nada aqui deve ser aplicado a sistemas de terceiros sem autorização.

---

## 1. Sumário executivo

Foram **confirmadas 10 vulnerabilidades**, todas reproduzidas contra a instância local, com requisição, evidência real e recomendação de correção documentadas. O resultado mostra falhas em **autorização** (BOLA, BFLA), **autenticação** (brute-force de OTP, forja de JWT), **exposição e manipulação de dados** (excessive data exposure, mass assignment), **requisições do servidor** (SSRF) e **injeção** (NoSQL, SQL) — além de um **encadeamento** que leva a execução de comando (RCE).

| Severidade | Qtde | Itens |
|---|---|---|
| 🔴 Crítica | 5 | Broken Authentication (OTP), SSRF, Forja de JWT, Shell Injection (chain), SQL Injection |
| 🟠 Alta | 5 | BOLA, Excessive Data Exposure, Mass Assignment, BFLA, NoSQL Injection |
| **Total** | **10** | |

**Destaque:** o item de **Shell Injection** não é uma falha isolada — é o encadeamento de **Mass Assignment + SSRF** para alcançar um ponto de injeção de comando interno. É o exemplo mais claro de como vulnerabilidades de severidade média, combinadas, produzem impacto crítico.

---

## 2. Tabela de findings

| # | Vulnerabilidade | Categoria OWASP API Top 10 (2023) | Severidade | Status | Detalhe |
|---|---|---|---|---|---|
| 1 | BOLA — localização de veículo | API1 — Broken Object Level Authorization | 🟠 Alta | Confirmado | [doc](vulnerabilidades/01-bola-localizacao-veiculo.md) |
| 2 | Broken Authentication — brute-force de OTP | API2 — Broken Authentication | 🔴 Crítica | Confirmado | [doc](vulnerabilidades/02-broken-authentication.md) |
| 3 | Excessive Data Exposure | API3 — Broken Object Property Level Authorization | 🟠 Alta | Confirmado | [doc](vulnerabilidades/03-excessive-data-exposure.md) |
| 4 | Mass Assignment | API3 — Broken Object Property Level Authorization | 🟠 Alta | Confirmado | [doc](vulnerabilidades/04-mass-assignment.md) |
| 5 | SSRF | API7 — Server-Side Request Forgery | 🔴 Crítica | Confirmado | [doc](vulnerabilidades/05-ssrf.md) |
| 6 | BFLA — função de admin por usuário comum | API5 — Broken Function Level Authorization | 🟠 Alta | Confirmado | [doc](vulnerabilidades/06-bfla.md) |
| 7 | Forja de JWT (assinatura não verificada) | API2 — Broken Authentication | 🔴 Crítica | Confirmado | [doc](vulnerabilidades/07-jwt-forgery.md) |
| 8 | Shell Injection (Mass Assignment + SSRF) | Cadeia API3 + API7 → injeção de comando | 🔴 Crítica | Confirmado | [doc](vulnerabilidades/08-shell-injection.md) |
| 9 | NoSQL Injection — cupom sem código | Injeção (era API8:2019) | 🟠 Alta | Confirmado | [doc](vulnerabilidades/09-nosql-injection.md) |
| 10 | SQL Injection — apply_coupon | Injeção (era API8:2019) | 🔴 Crítica | Confirmado | [doc](vulnerabilidades/10-sql-injection.md) |

---

## 3. Findings em detalhe (resumo)

1. **BOLA — localização de veículo** 🟠 — Com o próprio token, o atacante consulta a localização GPS do veículo de outro usuário (ID obtido via item 3). Falta verificação de propriedade do objeto. → *rastreamento físico de qualquer usuário.*
2. **Broken Authentication — OTP** 🔴 — O `check-otp` não tem rate limit e o OTP tem 4 dígitos (10.000 combinações); brute-force leva a **account takeover** sem acesso ao e-mail da vítima. → *tomada de conta.*
3. **Excessive Data Exposure** 🟠 — O endpoint de posts da comunidade vaza `email` e `vehicleid` de todos os usuários. Alimenta os itens 1 e 2. → *vazamento de PII + trampolim.*
4. **Mass Assignment** 🟠 — O cliente grava o campo `status` de um pedido e recebe reembolso sem devolver nada. → *fraude financeira.*
5. **SSRF** 🔴 — O `contact_mechanic` faz o servidor requisitar uma URL arbitrária; apontado a um serviço interno, retornou o conteúdo dele. → *acesso à rede interna.*
6. **BFLA** 🟠 — Um usuário comum chama um endpoint de admin e deleta o vídeo de outro usuário. → *operações privilegiadas por qualquer um.*
7. **Forja de JWT** 🔴 — O servidor não verifica a assinatura (aceita `alg:none` e payload adulterado); permite virar admin e personificar qualquer usuário. → *bypass total de autenticação.*
8. **Shell Injection (chain)** 🔴 — Mass Assignment grava um comando em `conversion_params`; a SSRF alcança o `convert_video` interno; o sink de injeção é atingido. → *RCE potencial.*
9. **NoSQL Injection** 🟠 — Um operador do MongoDB no `coupon_code` retorna um cupom válido sem saber o código. → *fraude + manipulação de query.*
10. **SQL Injection** 🔴 — O `coupon_code` entra cru em SQL (error-based e boolean-based confirmados). → *leitura/alteração de dados do banco.*

---

## 4. Temas recorrentes e recomendações prioritárias

- **Autorização no servidor, por objeto e por função** (itens 1, 6): validar propriedade/role em middleware central, negando por padrão.
- **Nunca confiar na entrada do cliente** (itens 3, 4, 7, 9, 10): allow-list de campos de saída e de escrita; validação de tipo; consultas parametrizadas; verificação de assinatura de JWT com algoritmo fixo.
- **Controlar o que o servidor acessa** (itens 5, 8): allow-list de destinos de requisição; endpoints internos inacessíveis a partir de entrada do usuário.
- **Proteger fluxos sensíveis** (item 2): rate limiting, bloqueio progressivo, OTP mais longo e com expiração.
- **Defesa em profundidade** (item 8): o maior impacto veio de encadeamento — corrigir cada elo, não só a falha "mais visível".

---

## 5. Scan automatizado (OWASP ZAP)

Um **ZAP Baseline Scan** (passivo) roda em CI contra uma instância efêmera do crAPI. Resultado: **0 High, 2 Medium** (CSP ausente, anti-clickjacking ausente), **7 Low** (headers CORS/X-Content-Type-Options, vazamento de versão do servidor, timestamp) e 2 Informational. O scan passivo complementa — não substitui — os testes manuais de lógica de autorização/negócio acima.

---

## 6. Conclusão

O crAPI, como esperado de um alvo de treino, concentra falhas representativas do OWASP API Security Top 10. A investigação cobriu as classes mais relevantes e demonstrou, com evidência reproduzível, desde falhas pontuais de autorização até um **encadeamento crítico (RCE)**. As recomendações da seção 4 resolvem a causa-raiz da maioria dos itens: autorização consistente no servidor, validação/parametrização de toda entrada e controle do que o backend acessa.

**Artefatos:** documentação por vulnerabilidade em [vulnerabilidades/](vulnerabilidades/) · [diagramas](diagramas.md) (arquitetura + encadeamento) · evidências reais em [../evidencias/](../evidencias/) · relatório HTML navegável em [../evidencias/relatorio-newman.html](../evidencias/relatorio-newman.html) · coleção Postman e scripts reprodutíveis em [../postman/](../postman/) e [../scripts/](../scripts/).
