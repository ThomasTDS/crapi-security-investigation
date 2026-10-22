🇧🇷 Português · [🇺🇸 English](en/fix-poc-sqli.md)

# PoC de correção — SQL Injection (apply_coupon)

Prova de que a vulnerabilidade de [SQL Injection](vulnerabilidades/10-sql-injection.md) pode ser **corrigida** — não só encontrada. Aplicamos o patch no serviço `workshop` do crAPI rodando localmente e revalidamos o ataque: antes funcionava, depois está neutralizado, e a funcionalidade legítima continua intacta.

> O crAPI é Apache-2.0. O patch ([`poc-correcao/apply-coupon-sqli.patch`](../poc-correcao/apply-coupon-sqli.patch)) incide sobre `services/workshop/crapi/shop/views.py` e é um exercício educacional de remediação.

---

## 1. A causa-raiz

Em `ApplyCouponView` (`services/workshop/crapi/shop/views.py`), o `coupon_code` enviado pelo cliente é **concatenado** direto na query SQL:

```python
cursor.execute(
    "SELECT coupon_code from applied_coupon WHERE user_id = "
    + str(user.id)
    + " AND coupon_code = '"
    + coupon_request_body["coupon_code"]
    + "'"
)
```

Qualquer aspa ou operador no `coupon_code` muda a estrutura da consulta — é injeção de SQL clássica.

## 2. A correção

Trocar a concatenação por uma **consulta parametrizada** (bind de parâmetros). A entrada do usuário passa a ser tratada como **valor**, nunca como fragmento de SQL:

```python
cursor.execute(
    "SELECT coupon_code FROM applied_coupon "
    "WHERE user_id = %s AND coupon_code = %s",
    [user.id, coupon_request_body["coupon_code"]],
)
```

Patch completo: [`poc-correcao/apply-coupon-sqli.patch`](../poc-correcao/apply-coupon-sqli.patch).

## 3. Como reproduzir (ambiente local)

Com o crAPI no ar (ver [ambiente](00-ambiente-crapi.md)), aplicar o patch no container do workshop e reiniciá-lo:

```bash
# 1) copiar o arquivo para fora do container
docker cp crapi-workshop:/app/crapi/shop/views.py views.py

# 2) aplicar o patch (ou editar manualmente conforme a secao 2)
patch views.py < poc-correcao/apply-coupon-sqli.patch

# 3) copiar de volta e reiniciar o servico
docker cp views.py crapi-workshop:/app/crapi/shop/views.py
docker restart crapi-workshop
```

> O patch também se aplica a um checkout do código-fonte do crAPI com `git apply poc-correcao/apply-coupon-sqli.patch` (seguido de rebuild da imagem).

## 4. Evidência (antes / depois)

Captura completa em [`poc-correcao/evidencia-antes-depois.txt`](../poc-correcao/evidencia-antes-depois.txt).

| Requisição | Antes (vulnerável) | Depois (corrigido) |
|---|---|---|
| `coupon_code: "TRAC075'"` | **HTTP 500** (query quebrada) | **400** `Coupon not found` |
| `coupon_code: "x' OR '1'='1"` | **400** citando `TRAC075` (injeção) | **400** `Coupon not found` |
| `coupon_code: "TRAC075"` (legítimo) | aplica / "já resgatado" | **400** "já resgatado" (função intacta) |

A aspa deixou de quebrar a query e o `OR '1'='1'` deixou de alterar o `WHERE` — a injeção foi eliminada, sem regressão no fluxo legítimo.

## 5. Lição

A correção é simples e definitiva: **nunca** montar SQL concatenando entrada do usuário; usar sempre parâmetros vinculados (prepared statements). O mesmo princípio vale para os demais pontos de entrada do projeto.
