🇧🇷 Português · [🇺🇸 English](en/environment-crapi.md)

# Ambiente — subindo o crAPI localmente

O crAPI é distribuído como um conjunto de contêineres orquestrados por **Docker Compose**. Esta página descreve como colocar o ambiente no ar e como validar que ele está pronto para os testes.

> Todos os testes deste repositório assumem o crAPI rodando **localmente**. Nunca execute os ataques descritos aqui contra ambientes que você não controla.

---

## 1. Pré-requisitos

- **Docker** (Engine 20.10+)
- **Docker Compose** (v2, embutido no Docker moderno via `docker compose`)
- ~4 GB de RAM livres para os contêineres
- Portas livres: `8888` (gateway web/API) e `8025` (MailHog, para capturar os e-mails/OTP enviados pela aplicação)

Verifique a instalação:

```bash
docker --version
docker compose version
```

---

## 2. Subindo o ambiente

O projeto oficial fornece um `docker-compose.yml` pronto. A forma recomendada pela OWASP:

```bash
# baixa o compose oficial mais recente
curl -o docker-compose.yml https://raw.githubusercontent.com/OWASP/crAPI/main/deploy/docker/docker-compose.yml

# sobe todos os serviços em segundo plano
docker compose -f docker-compose.yml --compatibility up -d
```

A primeira execução baixa várias imagens e pode levar alguns minutos.

> Este `docker-compose.yml` **não é versionado** neste repositório — ele pertence ao projeto crAPI e é baixado diretamente da fonte oficial, garantindo que você sempre use a versão atual e que este repo fique focado apenas na investigação de segurança.

---

## 3. Validando que o crAPI está no ar

- **Interface web:** acesse `http://localhost:8888`
- **Caixa de e-mail (MailHog):** acesse `http://localhost:8025` — é aqui que chegam os e-mails de verificação e os **OTPs** usados nos testes de autenticação.

Checagem rápida via linha de comando:

```bash
curl -i http://localhost:8888/
```

---

## 4. Criando as contas de teste

Vários ataques (BOLA, Broken Authentication, BFLA) exigem **duas contas** — a "vítima" e o "atacante" — para demonstrar que um usuário consegue acessar dados/funções de outro.

1. Na interface web, registre o **usuário A (vítima)** e, no cadastro, informe o número de um veículo. O crAPI envia um e-mail com o código do veículo — capture-o no MailHog (`http://localhost:8025`).
2. Registre o **usuário B (atacante)** da mesma forma.
3. Faça login com cada conta e guarde o **token JWT** retornado (ver abaixo) — ele será usado nas requisições autenticadas.

### Obtendo o token JWT

```bash
curl -s -X POST http://localhost:8888/identity/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"SEU_EMAIL","password":"SUA_SENHA"}'
```

A resposta contém o campo `token`. Use-o no header `Authorization: Bearer <token>` das demais requisições.

---

## 5. Variáveis de ambiente usadas no Postman

A coleção em [../postman/](../postman/) depende destas variáveis (definidas no environment):

| Variável | Descrição | Exemplo |
|---|---|---|
| `base_url` | URL base do crAPI | `http://localhost:8888` |
| `token_vitima` | JWT do usuário A | `eyJhbGci...` |
| `token_atacante` | JWT do usuário B | `eyJhbGci...` |
| `email_vitima` | e-mail do usuário A | `vitima@exemplo.com` |

---

## 6. Derrubando o ambiente

```bash
docker compose -f docker-compose.yml down

# para remover também os volumes (zera os dados)
docker compose -f docker-compose.yml down -v
```

---

## 7. Observações sobre versões dos endpoints

O crAPI evolui: alguns endpoints existem em versões `v2` e `v3`, e caminhos exatos podem mudar entre releases. Os paths citados na documentação de cada vulnerabilidade foram baseados na estrutura conhecida do projeto e **devem ser confirmados contra a sua instância** — a melhor fonte da verdade é o tráfego real capturado no Postman/DevTools ao usar a aplicação, além do código-fonte do crAPI.
