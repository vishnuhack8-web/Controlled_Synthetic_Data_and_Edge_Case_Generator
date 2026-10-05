#!/usr/bin/env bash
# Run the full pytest suite.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
[ -f .venv/bin/activate ] && source .venv/bin/activate
export PYTHONPATH="$ROOT/src"
python -m pytest -s tests/ "$@"
