#!/usr/bin/env bash
# ===================================================================
#  setup.sh - one-time setup for the CMIS Django project (Linux/macOS)
#  Creates a virtualenv, installs dependencies, migrates, and seeds.
# ===================================================================
set -euo pipefail
cd "$(dirname "$0")/.."

echo
echo "=========================================================="
echo "  Church Management Information System - Setup"
echo "=========================================================="
echo

PY=""
for candidate in python3 python; do
    if command -v "$candidate" >/dev/null 2>&1; then PY="$candidate"; break; fi
done
if [ -z "$PY" ]; then
    echo "ERROR: Python was not found on your PATH."
    echo "Install Python 3.10+ and try again."
    exit 1
fi

if [ ! -d ".venv" ]; then
    echo "[1/4] Creating virtual environment..."
    "$PY" -m venv .venv
else
    echo "[1/4] Virtual environment already exists - skipping."
fi

echo "[2/4] Installing dependencies..."
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip >/dev/null 2>&1 || true
python -m pip install -r requirements.txt

echo "[3/4] Applying database migrations..."
python manage.py migrate

echo "[4/4] Seeding demo data..."
python manage.py seed_demo || echo "WARNING: seeding failed; the app will run without demo data."

echo
echo "=========================================================="
echo "  Setup complete. Run ./scripts/start.sh to launch."
echo
echo "  Demo accounts (password: Demo@12345):"
echo "    superadmin  admin  pastor  finance  youthleader  member1"
echo "=========================================================="
echo
