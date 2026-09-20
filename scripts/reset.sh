#!/usr/bin/env bash
# ===================================================================
#  reset.sh - DESTRUCTIVE: wipe the database and reseed (Linux/macOS)
# ===================================================================
set -euo pipefail
cd "$(dirname "$0")/.."

echo
echo "*******************************************************"
echo "  WARNING: this deletes ALL data in the database."
echo "*******************************************************"
echo
read -r -p "Type yes to continue: " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "Aborted."
    exit 0
fi

if [ ! -d ".venv" ]; then
    echo "No virtual environment found. Run ./scripts/setup.sh first."
    exit 1
fi

# shellcheck disable=SC1091
source .venv/bin/activate
python start.py --reset --yes --no-run
