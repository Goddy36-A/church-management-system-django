#!/usr/bin/env bash
# ===================================================================
#  test.sh - run Django system checks and the test suite (Linux/macOS)
# ===================================================================
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -d ".venv" ]; then
    echo "No virtual environment found. Run ./scripts/setup.sh first."
    exit 1
fi

# shellcheck disable=SC1091
source .venv/bin/activate

echo "Running system checks..."
python manage.py check

echo
echo "Running test suite..."
python manage.py test
