#!/usr/bin/env bash
# Preflight environment validator (M0.5 / M1)
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "=== ExecLoop Preflight Validation ==="

# Check Python environment
if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 is required but not found." >&2
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "Python version: $PYTHON_VERSION"

# Check required commands
for cmd in git jq pdftotext pdftoppm pdflatex; do
    if command -v "$cmd" &>/dev/null; then
        echo "  [OK] $cmd found"
    else
        echo "  [WARN] $cmd not found in PATH"
    fi
done

# Validate Python contracts and handoff
echo "--- Running fast contracts & handoff checks ---"
python3 -m unittest -q control.test_contracts control.test_ai_handoff

echo "=== Preflight OK ==="
