#!/usr/bin/env bash
# Fast, local M11/M12 integrity check. It never starts Prime Agent or a model.
set -Eeuo pipefail
IFS=$'\n\t'

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd -P)"

if [[ ! -f "$ROOT/AGENTS.md" ]]; then
    echo "Not an article-loop project root: $ROOT" >&2
    exit 1
fi

exec python3 "$ROOT/scripts/article_loop_command.py" check --root "$ROOT"
