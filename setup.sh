#!/usr/bin/env bash
set -e

echo "== NetGuard AI setup (macOS/Linux) =="
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo
echo "[1/4] Creating backend virtual environment..."
cd "$ROOT/backend"
python3 -m venv .venv
[ -f .env ] || cp .env.example .env

echo
echo "[2/4] Installing backend dependencies..."
./.venv/bin/python -m pip install --upgrade pip --quiet
./.venv/bin/python -m pip install -r requirements.txt

echo
echo "[3/4] Installing frontend dependencies..."
cd "$ROOT/frontend"
[ -f .env ] || cp .env.example .env
npm install

echo
echo "[4/4] Done."
cd "$ROOT"
echo "Run './run.sh' to start both servers, or see README.md for manual steps."
