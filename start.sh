#!/usr/bin/env bash
# CyberShield KZ — однокомандный запуск (Linux / macOS)
#   ./start.sh                       — поднять сервер на http://localhost:8000
#   ./start.sh --port 9000           — любые флаги пробрасываются в uvicorn
#   FORCE_INSTALL=1 ./start.sh       — переустановить зависимости
set -e

cd "$(dirname "$0")"

PY="${PYTHON:-python3}"
VENV="venv"
MARKER="$VENV/.deps_installed"

# 1. venv
if [ ! -d "$VENV" ]; then
    echo ">>> Создаю виртуальное окружение ($VENV)..."
    "$PY" -m venv "$VENV"
fi

# shellcheck disable=SC1091
source "$VENV/bin/activate"

# 2. Зависимости (ставим если маркера нет или requirements.txt новее)
if [ -n "$FORCE_INSTALL" ] || [ ! -f "$MARKER" ] || [ "requirements.txt" -nt "$MARKER" ]; then
    echo ">>> Устанавливаю зависимости из requirements.txt..."
    pip install --upgrade pip -q
    pip install -r requirements.txt
    touch "$MARKER"
fi

# 3. .env (если есть)
if [ -f ".env" ]; then
    set -a
    # shellcheck disable=SC1091
    source .env
    set +a
fi

# 4. Дефолтный DATABASE_URL (если не задан)
export DATABASE_URL="${DATABASE_URL:-postgresql://postgres:postgres@localhost:5432/cybershield}"

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"

echo ""
echo "================================================================"
echo "  CyberShield KZ"
echo "  URL:      http://localhost:$PORT"
echo "  Database: $DATABASE_URL"
echo "================================================================"
echo ""

exec uvicorn app.main:app --host "$HOST" --port "$PORT" "$@"
