#!/bin/sh
# Validate the checkout-local canonical CPython runtime without creating it.
set -eu

if [ "$#" -ne 1 ]; then
    echo "usage: bin/python-runtime.sh ROOT" >&2
    exit 2
fi
ROOT=$1
VERSION_FILE="$ROOT/.python-version"
PYTHON="$ROOT/.venv/bin/python"

if [ -L "$VERSION_FILE" ] || [ ! -f "$VERSION_FILE" ] || [ "$(cat "$VERSION_FILE")" != "3.14" ]; then
    echo "Canonical runtime declaration is missing or invalid; expected .python-version = 3.14." >&2
    exit 1
fi
if [ -L "$ROOT/.venv" ] || [ ! -d "$ROOT/.venv" ] || [ ! -x "$PYTHON" ]; then
    echo "Canonical .venv is missing or broken. Recreate it with: bash bin/bootstrap-deps.sh" >&2
    exit 1
fi

if ! "$PYTHON" - "$ROOT" <<'PY'
from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve()
expected = (root / ".venv").resolve()
valid = (
    sys.implementation.name == "cpython"
    and sys.version_info[:2] == (3, 14)
    and Path(sys.prefix).resolve() == expected
    and Path(sys.base_prefix).resolve() != expected
)
raise SystemExit(0 if valid else 1)
PY
then
    echo "Canonical .venv must be a CPython 3.14 environment for this checkout. Recreate it with: bash bin/bootstrap-deps.sh" >&2
    exit 1
fi
