#!/usr/bin/env bash
# Start the M14 Control Center only through its canonical loopback server.
set -Eeuo pipefail
IFS=$'\n\t'

PORT=8765
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
SCRIPT_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd -P)"
ROOT="$(pwd -P)"

usage() {
    cat <<'EOF'
Usage: bash bin/start-control-center.sh [--port PORT]

Run this command from the article-loop project root. PORT must be 1024-65535
and defaults to 8765. The Control Center always binds to 127.0.0.1.
EOF
}

while (($# > 0)); do
    case "$1" in
        --port)
            if (($# < 2)); then
                echo "--port requires a value" >&2
                exit 2
            fi
            PORT="$2"
            shift 2
            ;;
        --help)
            usage
            exit 0
            ;;
        *)
            echo "unsupported Control Center launcher argument: $1" >&2
            exit 2
            ;;
    esac
done

if [[ "$ROOT" != "$SCRIPT_ROOT" || ! -f "$ROOT/PLANS.md" || ! -f "$ROOT/.prime/agent/skills/article-loop/src/article_loop/control_center.py" ]]; then
    echo "run bin/start-control-center.sh from a valid article-loop project root" >&2
    exit 1
fi

if [[ ! "$PORT" =~ ^[0-9]+$ ]]; then
    echo "--port must be an integer from 1024 to 65535" >&2
    exit 2
fi
PORT=$((10#$PORT))
if ((PORT < 1024 || PORT > 65535)); then
    echo "--port must be an integer from 1024 to 65535" >&2
    exit 2
fi

export PYTHONPATH="$ROOT/.prime/agent/skills/article-loop/src"
exec python3 -m article_loop.control_center --root "$ROOT" --host 127.0.0.1 --port "$PORT"
