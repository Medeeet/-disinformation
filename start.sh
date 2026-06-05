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

# Порт бос па, жоқ па тексеру (бос болса — 0 емес код қайтарады)
port_in_use() { (echo > "/dev/tcp/127.0.0.1/$1") >/dev/null 2>&1; }

# Берілген порттан бастап бірінші бос портты табу
find_free_port() {
    local p="$1" tries=0
    while port_in_use "$p" && [ "$tries" -lt 50 ]; do
        p=$((p + 1)); tries=$((tries + 1))
    done
    echo "$p"
}

# 1. Виртуалды орта
if [ ! -d "$VENV" ]; then
    echo ">>> Виртуалды орта жасалуда ($VENV)..."
    "$PY" -m venv "$VENV"
fi

# shellcheck disable=SC1091
source "$VENV/bin/activate"

# 2. Тәуелділіктер (маркер жоқ болса немесе requirements.txt жаңарақ болса орнатылады)
if [ -n "$FORCE_INSTALL" ] || [ ! -f "$MARKER" ] || [ "requirements.txt" -nt "$MARKER" ]; then
    echo ">>> requirements.txt тәуелділіктері орнатылуда..."
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

# 4. Әдепкі DATABASE_URL (берілмесе)
export DATABASE_URL="${DATABASE_URL:-postgresql://postgres:postgres@localhost:5432/cybershield}"

# 5. Docker арқылы PostgreSQL (орнатылған болса) — жергілікті дерекқор үшін
if [ -z "$SKIP_DOCKER" ] && [ -f "docker-compose.yml" ] \
        && command -v docker >/dev/null 2>&1 \
        && [[ "$DATABASE_URL" == *"localhost"* || "$DATABASE_URL" == *"127.0.0.1"* ]]; then
    if docker info >/dev/null 2>&1; then
        # Postgres үшін бос портты табу (5432 бос емес болса — келесісі)
        DESIRED_DB_PORT="${POSTGRES_PORT:-5432}"
        DB_PORT="$(find_free_port "$DESIRED_DB_PORT")"
        if [ "$DB_PORT" != "$DESIRED_DB_PORT" ]; then
            echo ">>> $DESIRED_DB_PORT порты бос емес — Postgres $DB_PORT портында іске қосылады"
        fi
        export POSTGRES_PORT="$DB_PORT"
        # DATABASE_URL ішіндегі портты жаңасына ауыстыру (қалған бөлігі сақталады)
        DATABASE_URL="$(echo "$DATABASE_URL" | sed -E "s#(@[^:/]+):[0-9]+#\1:$DB_PORT#")"
        export DATABASE_URL

        echo ">>> PostgreSQL Docker арқылы іске қосылуда (порт $DB_PORT)..."
        if ! docker compose up -d --wait 2>/dev/null; then
            # --wait қолдамайтын ескі docker compose
            docker compose up -d
            echo ">>> Postgres жауап бергенше күтілуде..."
            for _ in $(seq 1 30); do
                if port_in_use "$DB_PORT"; then break; fi
                sleep 1
            done
        fi
    else
        echo "[ЕСКЕРТУ] Docker орнатылған, бірақ демоны іске қосылмаған. Docker Desktop-ты іске қосыңыз немесе Postgres-ті қолмен көтеріңіз."
    fi
fi

# 6. Қосымша порты (бос емес болса — келесі бос порт)
HOST="${HOST:-0.0.0.0}"
DESIRED_PORT="${PORT:-8000}"
APP_PORT="$(find_free_port "$DESIRED_PORT")"
if [ "$APP_PORT" != "$DESIRED_PORT" ]; then
    echo ">>> $DESIRED_PORT порты бос емес — қосымша $APP_PORT портында іске қосылады"
fi

echo ""
echo "================================================================"
echo "  CyberShield KZ"
echo "  Мекенжай:  http://localhost:$APP_PORT"
echo "  Дерекқор:  $DATABASE_URL"
echo "================================================================"
echo ""

exec uvicorn app.main:app --host "$HOST" --port "$APP_PORT" "$@"
