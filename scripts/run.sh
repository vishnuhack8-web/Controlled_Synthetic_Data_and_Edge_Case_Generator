#!/usr/bin/env bash
# Start the SynthEdge backend (serves the API and the built-in dashboard).
# Usage: ./scripts/run.sh            -> backend only (http://localhost:8000)
#        ./scripts/run.sh --all      -> backend + Next.js frontend (http://localhost:3000)
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

[ -f .venv/bin/activate ] && source .venv/bin/activate
export PYTHONPATH="$ROOT/src"

echo "==================================================="
echo "  Starting SynthEdge AI Platform"
echo "==================================================="

if [ "${1:-}" = "--all" ]; then
  (cd src/frontend && npm run dev) &
  FRONTEND_PID=$!
  trap 'kill $FRONTEND_PID 2>/dev/null || true' EXIT
fi

echo "[INFO] Backend API + dashboard: http://localhost:8000"
python -m backend.main
