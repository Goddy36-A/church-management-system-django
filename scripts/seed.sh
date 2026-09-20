#!/usr/bin/env bash
# ===================================================================
#  seed.sh - load fictional demo data into the database (Linux/macOS)
# ===================================================================
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -d ".venv" ]; then
    echo "No virtual environment found. Run ./scripts/setup.sh first."
    exit 1
fi

# shellcheck disable=SC1091
source .venv/bin/activate
python manage.py seed_demo

echo
echo "Demo accounts (password: Demo@12345):"
echo "  superadmin  admin  pastor  finance  youthleader  member1"
echo
