#!/usr/bin/env bash
set -euo pipefail

# CodeSentinel Idempotent VM Bootstrap Script
# Usage: ./bootstrap.sh [--check]

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

CHECK_ONLY=0
if [ "${1:-}" = "--check" ]; then
    CHECK_ONLY=1
fi

log() {
    echo "[bootstrap] $*"
}

check_status=0

# 1. Python check / install
check_python() {
    if command -v python3 >/dev/null 2>&1; then
        PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        PY_MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
        PY_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')
        if [ "$PY_MAJOR" -ge 3 ] && [ "$PY_MINOR" -ge 12 ]; then
            log "Python $PY_VER detected (>= 3.12): OK"
            return 0
        fi
    fi
    return 1
}

if [ "$CHECK_ONLY" -eq 1 ]; then
    if ! check_python; then
        echo "[check] Python >= 3.12: MISSING"
        check_status=1
    else
        echo "[check] Python >= 3.12: OK"
    fi
else
    if ! check_python; then
        log "Installing Python 3 and venv..."
        if [ "$(id -u)" -eq 0 ]; then
            apt-get update && apt-get install -y python3 python3-venv python3-pip sqlite3
        elif sudo -n true 2>/dev/null; then
            sudo apt-get update && sudo apt-get install -y python3 python3-venv python3-pip sqlite3
        else
            log "Warning: Cannot install system packages without root/sudo."
        fi
    fi
fi

# 2. Node & npm check / install
check_node() {
    if command -v node >/dev/null 2>&1 && command -v npm >/dev/null 2>&1; then
        NODE_VER=$(node -v)
        log "Node.js $NODE_VER and npm detected: OK"
        return 0
    fi
    return 1
}

if [ "$CHECK_ONLY" -eq 1 ]; then
    if ! check_node; then
        echo "[check] Node.js and npm: MISSING"
        check_status=1
    else
        echo "[check] Node.js and npm: OK"
    fi
else
    if ! check_node; then
        log "Node.js / npm missing. Installing..."
        if [ "$(id -u)" -eq 0 ]; then
            apt-get update && apt-get install -y nodejs npm
        elif sudo -n true 2>/dev/null; then
            sudo apt-get update && sudo apt-get install -y nodejs npm
        else
            log "Warning: Cannot install node/npm without root/sudo."
        fi
    fi
fi

# 3. Virtualenv setup
check_venv() {
    if [ -f "$PROJECT_ROOT/.venv/bin/python" ] && [ -f "$PROJECT_ROOT/.venv/bin/uvicorn" ]; then
        return 0
    fi
    return 1
}

if [ "$CHECK_ONLY" -eq 1 ]; then
    if ! check_venv; then
        echo "[check] Virtualenv (.venv) with dependencies: MISSING"
        check_status=1
    else
        echo "[check] Virtualenv (.venv) with dependencies: OK"
    fi
else
    if [ ! -d "$PROJECT_ROOT/.venv" ]; then
        log "Creating virtual environment at .venv..."
        python3 -m venv "$PROJECT_ROOT/.venv"
    fi
    log "Ensuring Python dependencies are installed..."
    "$PROJECT_ROOT/.venv/bin/pip" install --upgrade pip --quiet
    "$PROJECT_ROOT/.venv/bin/pip" install -e ".[dev]" --quiet
fi

# 4. Console build
check_console() {
    if [ -f "$PROJECT_ROOT/console/dist/index.html" ]; then
        return 0
    fi
    return 1
}

if [ "$CHECK_ONLY" -eq 1 ]; then
    if ! check_console; then
        echo "[check] Built console UI (console/dist/index.html): MISSING"
        check_status=1
    else
        echo "[check] Built console UI (console/dist/index.html): OK"
    fi
else
    if [ -d "$PROJECT_ROOT/console" ]; then
        if [ ! -d "$PROJECT_ROOT/console/node_modules" ]; then
            log "Installing console npm dependencies..."
            (cd "$PROJECT_ROOT/console" && npm install --quiet)
        fi
        log "Building console UI..."
        (cd "$PROJECT_ROOT/console" && npm run build)
    fi
fi

# 5. Database initialization
check_db() {
    local db_file="${DATABASE_PATH:-$HOME/codesentinel-ai/codesentinel.db}"
    if [ -f "$db_file" ]; then
        return 0
    fi
    return 1
}

if [ "$CHECK_ONLY" -eq 1 ]; then
    if ! check_db; then
        echo "[check] Initialized SQLite Database: MISSING"
        check_status=1
    else
        echo "[check] Initialized SQLite Database: OK"
    fi
else
    log "Initializing SQLite database..."
    "$PROJECT_ROOT/.venv/bin/python" -c "from codesentinel.api.database import init_db; init_db()"
fi

# 6. Systemd unit configuration
check_systemd() {
    if [ -f "/etc/systemd/system/codesentinel-console.service" ] && \
       [ -f "/etc/systemd/system/codesentinel-daemon.service" ]; then
        return 0
    fi
    if [ -f "$HOME/.config/systemd/user/codesentinel-console.service" ] && \
       [ -f "$HOME/.config/systemd/user/codesentinel-daemon.service" ]; then
        return 0
    fi
    return 1
}

if [ "$CHECK_ONLY" -eq 1 ]; then
    if ! check_systemd; then
        echo "[check] Systemd unit files installed: MISSING (available in systemd/)"
        check_status=1
    else
        echo "[check] Systemd unit files installed: OK"
    fi
else
    if [ -d "$PROJECT_ROOT/systemd" ]; then
        if [ "$(id -u)" -eq 0 ]; then
            log "Configuring systemd service units in /etc/systemd/system/..."
            cp "$PROJECT_ROOT/systemd/"*.service /etc/systemd/system/
            systemctl daemon-reload
            systemctl enable codesentinel-console.service codesentinel-daemon.service || true
        elif sudo -n true 2>/dev/null; then
            log "Configuring systemd service units in /etc/systemd/system/ via sudo..."
            sudo cp "$PROJECT_ROOT/systemd/"*.service /etc/systemd/system/
            sudo systemctl daemon-reload
            sudo systemctl enable codesentinel-console.service codesentinel-daemon.service || true
        else
            log "Note: sudo access not passwordless; configuring user systemd units under ~/.config/systemd/user/..."
            mkdir -p "$HOME/.config/systemd/user"
            cp "$PROJECT_ROOT/systemd/"*.service "$HOME/.config/systemd/user/"
            if command -v systemctl >/dev/null 2>&1; then
                systemctl --user daemon-reload || true
            fi
        fi
    fi
fi

if [ "$CHECK_ONLY" -eq 1 ]; then
    if [ "$check_status" -eq 0 ]; then
        echo "[check] All bootstrap requirements satisfied."
        exit 0
    else
        echo "[check] One or more components need bootstrap."
        exit 1
    fi
fi

log "Bootstrap completed successfully."
