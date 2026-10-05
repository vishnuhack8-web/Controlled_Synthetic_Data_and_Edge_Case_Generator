#!/usr/bin/env bash
# One-time setup: Python venv, backend deps, frontend deps, .env file.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "==> Creating Python virtual environment (.venv)"
python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate

echo "==> Installing backend dependencies"
pip install --upgrade pip
pip install -r src/backend/requirements.txt

if command -v npm >/dev/null 2>&1; then
  echo "==> Installing frontend dependencies"
  (cd src/frontend && npm install)
else
  echo "[WARN] npm not found - skipping frontend install (Node.js 18+ required)"
fi

if [ ! -f .env ]; then
  cp .env.example .env
  echo "==> Created .env from .env.example"
fi

echo "Setup complete. Start the platform with: ./scripts/run.sh"
