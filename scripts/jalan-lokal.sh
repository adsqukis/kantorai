#!/usr/bin/env bash
# Jalankan semuanya di komputer sendiri (macOS/Linux):
#   dashboard  http://localhost:8710   (password bawaan: qukis)
#   kantor 3D  http://localhost:8712/office
#   runtime    http://127.0.0.1:8711   (dibaca kantor 3D)
#
#   ./scripts/jalan-lokal.sh --demo     # pakai data CONTOH, tanpa token
#   ./scripts/jalan-lokal.sh            # pakai data asli dari .lokal/env (token + API key)
#
# Butuh: Python 3.12+, Node.js 20+, npm.
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT=$PWD
DEMO=0
BERJALAN=""
for arg in "$@"; do
  case "$arg" in
    --demo) DEMO=1 ;;
    --berjalan) BERJALAN="--berjalan" ;;
  esac
done

mkdir -p .lokal
export DB_PATH="${DB_PATH:-$ROOT/.lokal/laporan.db}"
export CONFIG_DIR="$ROOT/config"
export COOKIE_SECURE=false
export DASHBOARD_PASSWORD="${DASHBOARD_PASSWORD:-qukis}"
if [ ! -f .lokal/session_secret ]; then
  python3 -c "import secrets;print(secrets.token_hex(32))" > .lokal/session_secret
fi
export SESSION_SECRET="${SESSION_SECRET:-$(cat .lokal/session_secret)}"
# Token & API key asli (opsional): salin .env.example ke .lokal/env lalu isi.
if [ -f .lokal/env ]; then set -a; . ./.lokal/env; set +a; fi

echo "== Menyiapkan Python"
[ -x .venv/bin/python ] || python3 -m venv .venv
.venv/bin/pip install -q -e . >/dev/null

echo "== Menyiapkan kantor 3D (pertama kali bisa beberapa menit)"
(cd kantor3d && { [ -d node_modules ] || npm ci --no-audit --no-fund; } && { [ -d .next ] || npm run build; })

if [ "$DEMO" = 1 ]; then .venv/bin/laporan demo $BERJALAN; fi

PIDS=()
cleanup() { kill "${PIDS[@]}" 2>/dev/null || true; }
trap cleanup EXIT INT TERM

.venv/bin/laporan runtime --port 8711 > .lokal/runtime.log 2>&1 & PIDS+=($!)
.venv/bin/laporan serve --host 127.0.0.1 --port 8710 > .lokal/dashboard.log 2>&1 & PIDS+=($!)
(
  cd kantor3d
  HOST=127.0.0.1 PORT=8712 \
  CLAW3D_GATEWAY_URL=http://127.0.0.1:8711 CLAW3D_GATEWAY_ADAPTER_TYPE=custom \
  CUSTOM_RUNTIME_ALLOWLIST=127.0.0.1,localhost \
  OPENCLAW_STATE_DIR="$ROOT/.lokal/kantor3d-state" \
  NODE_ENV=production node server/index.js
) > .lokal/kantor3d.log 2>&1 & PIDS+=($!)

sleep 4
cat <<INFO

Siap.
  Dashboard  : http://localhost:8710   (password: $DASHBOARD_PASSWORD)
  Kantor 3D  : http://localhost:8712/office   (klik Connect bila diminta)
  Log        : .lokal/*.log
Tekan Ctrl+C untuk berhenti.
INFO
wait
