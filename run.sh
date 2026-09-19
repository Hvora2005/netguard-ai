#!/usr/bin/env bash
# Starts the backend and frontend dev servers. Ctrl+C stops both.
set -e
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cleanup() {
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
}
trap cleanup EXIT

(cd "$ROOT/backend" && ./.venv/bin/uvicorn app.main:app --reload) &
BACKEND_PID=$!

(cd "$ROOT/frontend" && npm run dev) &
FRONTEND_PID=$!

echo "Backend at http://localhost:8000 (docs at /docs)"
echo "Frontend at http://localhost:5173"

wait
