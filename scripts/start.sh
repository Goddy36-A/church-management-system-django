#!/usr/bin/env bash
# ===================================================================
#  start.sh - launch the CMIS development server (Linux/macOS)
#  Arguments are passed through to start.py, e.g.
#      ./scripts/start.sh --port 8080
# ===================================================================
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -d ".venv" ]; then
    echo "No virtual environment found. Run ./scripts/setup.sh first."
    exit 1
fi

# shellcheck disable=SC1091
source .venv/bin/activate
exec python start.py "$@"
