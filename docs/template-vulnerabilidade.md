🇧🇷 Português · [🇺🇸 English](en/vulnerability-template.md)

# Template — documentação de vulnerabilidade

Modelo seguido por todos os documentos em [vulnerabilidades/](vulnerabilidades/). Copie este arquivo ao documentar uma nova falha.

---

## <Nome da vulnerabilidade>

**Categoria OWASP API Security Top 10 (2023):** `APIx — <nome da categoria>`
**Severidade estimada:** `Crítica | Alta | Média | Baixa`
**Desafio crAPI correspondente:** `<número/descrição do desafio oficial>`

### 1. Resumo

Uma a três frases explicando, em linguagem simples, qual é a falha e o que um atacante consegue fazer.

### 2. Pré-condições

- Contas necessárias (ex.: vítima + atacante)
- Tokens/estado necessários
- Dados que precisam ser coletados antes (ex.: ID de um recurso de outro usuário)

### 3. Passo a passo da exploração

Descrição numerada do ataque, incluindo a(s) requisição(ões) exata(s):

```http
MÉTODO /caminho/do/endpoint HTTP/1.1
Host: localhost:8888
Authorization: Bearer <token>
Content-Type: application/json

{ "corpo": "da requisição" }
```

### 4. Evidência

Referência ao print salvo em `evidencias/<slug-da-vuln>/` e um resumo do que a resposta prova (ex.: "a resposta retornou os dados do usuário B mesmo autenticado como usuário A").

### 5. Por que é um risco

Explicação do impacto **de negócio**, não só técnico: que dado vaza, que dano o atacante causa, por que importa.

### 6. Como corrigir

Recomendação objetiva de mitigação (controle de autorização por objeto, rate limiting, allow-list de propriedades, etc.).

### 7. Referências

- Link para a categoria correspondente no OWASP API Security Top 10
