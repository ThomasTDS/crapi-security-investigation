# Evidências

Uma subpasta por vulnerabilidade, com os prints das respostas que comprovam cada falha (capturados do Postman ao reproduzir os ataques contra o crAPI local).

| Pasta | Vulnerabilidade |
|---|---|
| `01-bola/` | BOLA — localização de veículo |
| `02-broken-authentication/` | Broken Authentication — brute-force de OTP |
| `03-excessive-data-exposure/` | Excessive Data Exposure |
| `04-mass-assignment/` | Mass Assignment |
| `05-ssrf/` | SSRF |
| `06-bfla/` | BFLA |
| `07-jwt-forgery/` | Forja de JWT (assinatura não verificada) |
| `08-shell-injection/` | Shell Injection (Mass Assignment + SSRF) |

Convenção de nome dos arquivos: `NN-descricao.png` (ex.: `01-resposta-200-veiculo-vitima.png`).

> As pastas começam vazias (apenas `.gitkeep`) e são preenchidas na fase de execução, quando o crAPI estiver rodando localmente.
