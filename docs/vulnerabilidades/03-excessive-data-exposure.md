🇧🇷 Português · [🇺🇸 English](../en/vulnerabilities/03-excessive-data-exposure.md)

# Excessive Data Exposure — Endpoint que vaza dados de outros usuários

**Categoria OWASP API Security Top 10 (2023):** `API3 — Broken Object Property Level Authorization (Excessive Data Exposure)`
**Severidade estimada:** `Alta`
**Desafio crAPI correspondente:** Challenge 4 — "find an endpoint that leaks sensitive information of other users"

---

## 1. Resumo

Um endpoint retorna **mais campos do que a interface usa**. Ao listar itens públicos (como posts da comunidade/fórum), a API inclui no JSON dados sensíveis dos autores — e-mail, número de telefone, `vehicleId`, etc. — que a tela nunca mostra. O atacante lê esses dados diretamente na resposta.

## 2. Pré-condições

- Conta autenticada qualquer (os posts da comunidade são visíveis a usuários logados).

## 3. Passo a passo da exploração

1. Autentique-se e liste os posts recentes da comunidade:

```http
GET /community/api/v2/community/posts/recent HTTP/1.1
Host: localhost:8888
Authorization: Bearer <token>
```

2. Inspecione o JSON retornado. Além do conteúdo do post, a resposta tende a incluir, para cada autor, um objeto com campos como `email`, `vehicleid`, `profile_pic_url`, `nickname` — dados que a interface não exibe.

3. Esses campos vazados alimentam outros ataques: o `email` habilita o [brute-force de OTP](02-broken-authentication.md); o `vehicleid` habilita o [BOLA de localização](01-bola-localizacao-veiculo.md).

## 4. Evidência

**Confirmado contra a instância local** — captura em [`evidencias/03-excessive-data-exposure/captura.txt`](../../evidencias/03-excessive-data-exposure/captura.txt).

A resposta de `GET /community/api/v2/community/posts/recent` inclui, para cada autor, um objeto com campos sensíveis que a tela do fórum nunca exibe:

```json
"author": {
  "nickname": "Adam",
  "email": "adam007@example.com",
  "vehicleid": "f89b5f21-7829-45cb-a650-299a61090378"
}
```

O `email` e o `vehicleid` vazados aqui foram usados diretamente nos ataques de [BOLA](01-bola-localizacao-veiculo.md) e de [brute-force de OTP](02-broken-authentication.md).

## 5. Por que é um risco

O servidor delega ao cliente a responsabilidade de "não mostrar" dados sensíveis — mas quem consome a API vê o JSON inteiro. Isso vaza PII (dados pessoais) de todos os usuários e serve de **trampolim para outros ataques** (o e-mail e o ID de veículo coletados aqui são insumo direto de BOLA e account takeover). É um erro de design comum: serializar o objeto inteiro do banco em vez de um DTO enxuto.

## 6. Como corrigir

- Retornar apenas os campos estritamente necessários para cada resposta (**allow-list** / DTOs específicos por endpoint), nunca o objeto completo do banco.
- Nunca confiar no cliente para filtrar dados sensíveis.
- Revisar respostas de endpoints de listagem, onde o vazamento costuma passar despercebido por repetir-se para muitos registros.

## 7. Referências

- [API3:2023 Broken Object Property Level Authorization](https://owasp.org/API-Security/editions/2023/en/0xa3-broken-object-property-level-authorization/)
