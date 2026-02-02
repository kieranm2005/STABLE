#!/bin/bash
set -e

REPO_URL="https://github.com/kieranm2005/STABLE.git"
APP_DIR="/home/ta-pi/STABLE"
BRANCH="main"
CHECK_INTERVAL=100

ensure_repo() {
    if [ ! -d "$APP_DIR/.git" ]; then
        mkdir -p "$APP_DIR"
        git clone "$REPO_URL" "$APP_DIR"
    fi
}

ensure_venv() {
    if [ ! -d "$APP_DIR/venv" ]; then
        python3 -m venv "$APP_DIR/venv"
    fi
}

install_requirements() {
    "$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements.txt"
}

start_app() {
    "$APP_DIR/venv/bin/python" "$APP_DIR/src/main.py" &
    APP_PID=$!
}

stop_app() {
    if [ -n "${APP_PID:-}" ]; then
        kill "$APP_PID" 2>/dev/null || true
        wait "$APP_PID" 2>/dev/null || true
    fi
}

update_available() {
    git fetch origin "$BRANCH" >/dev/null 2>&1
    LOCAL_REV=$(git rev-parse HEAD)
    REMOTE_REV=$(git rev-parse "origin/$BRANCH")
    [ "$LOCAL_REV" != "$REMOTE_REV" ]
}

ensure_repo
cd "$APP_DIR"

git pull origin "$BRANCH"

ensure_venv
install_requirements
start_app

LAST_CHECK=$(date +%s)

while true; do
    sleep 5

    if ! kill -0 "$APP_PID" 2>/dev/null; then
        start_app
    fi

    NOW=$(date +%s)
    if [ $((NOW - LAST_CHECK)) -ge "$CHECK_INTERVAL" ]; then
        LAST_CHECK=$NOW
        if update_available; then
            stop_app
            git pull origin "$BRANCH"
            install_requirements
            start_app
        fi
    fi
done