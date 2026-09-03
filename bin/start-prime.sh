#!/usr/bin/env bash
# Start only an explicitly authorized, project-local Prime Agent session.
set -Eeuo pipefail
IFS=$'\n\t'

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
DEFAULT_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd -P)"
ROOT="$DEFAULT_ROOT"
TEMPLATE="article-run"
MODE="dry-run"
MODE_EXPLICIT=0
AUTHORIZED=0

usage() {
    cat <<'EOF'
Usage: bash bin/start-prime.sh [--root PATH] [--template NAME] [--dry-run]
       bash bin/start-prime.sh --live --authorize-live [--root PATH]

The default is a local dry-run. Live mode requires explicit authorization,
fail-closed budget/configuration, a clean local preflight, and prime-agent in PATH.
EOF
}

while (($# > 0)); do
    case "$1" in
        --root)
            if (($# < 2)); then
                echo "--root requires a path" >&2
                exit 2
            fi
            ROOT="$2"
            shift 2
            ;;
        --template)
            if (($# < 2)); then
                echo "--template requires a name" >&2
                exit 2
            fi
            TEMPLATE="$2"
            shift 2
            ;;
        --dry-run)
            if [[ "$MODE_EXPLICIT" == 1 && "$MODE" != "dry-run" ]]; then
                echo "--dry-run and --live are mutually exclusive" >&2
                exit 2
            fi
            MODE="dry-run"
            MODE_EXPLICIT=1
            shift
            ;;
        --live)
            if [[ "$MODE_EXPLICIT" == 1 && "$MODE" != "live" ]]; then
                echo "--dry-run and --live are mutually exclusive" >&2
                exit 2
            fi
            MODE="live"
            MODE_EXPLICIT=1
            shift
            ;;
        --authorize-live)
            AUTHORIZED=1
            shift
            ;;
        --help)
            usage
            exit 0
            ;;
        *)
            echo "unsupported launcher argument: $1" >&2
            exit 2
            ;;
    esac
done

if [[ "$MODE" == "dry-run" && "$AUTHORIZED" == 1 ]]; then
    echo "--authorize-live requires --live" >&2
    exit 2
fi

case "$TEMPLATE" in
    article-bootstrap|article-preflight|article-run|article-status|article-checkpoint|article-pause|article-resume|article-stop|article-finalize)
        ;;
    *)
        echo "unsupported project template: $TEMPLATE" >&2
        exit 2
        ;;
esac

if [[ -L "$ROOT" || ! -d "$ROOT" ]]; then
    echo "root must be an existing non-symlink directory: $ROOT" >&2
    exit 1
fi
ROOT="$(cd -- "$ROOT" && pwd -P)"

bash "$ROOT/bin/check.sh"
python3 "$ROOT/scripts/article_loop_command.py" preflight --root "$ROOT"

if [[ -e "$ROOT/control/STOP" || -L "$ROOT/control/STOP" ]]; then
    echo "control/STOP blocks new operations" >&2
    exit 1
fi

if [[ "$MODE" == "dry-run" ]]; then
    python3 - "$ROOT" "$TEMPLATE" <<'PY'
import json
import sys

print(json.dumps({
    "status": "dry_run",
    "root": sys.argv[1],
    "template": sys.argv[2],
    "prime_started": False,
    "model_called": False,
}))
PY
    exit 0
fi

if [[ "$AUTHORIZED" != 1 ]]; then
    echo "live mode requires --authorize-live" >&2
    exit 1
fi

# M11 consumes the already versioned fail-closed budget declaration. It does
# not change it, and it cannot turn live execution on by itself.
python3 "$ROOT/scripts/article_loop_command.py" check --root "$ROOT" --require-live

# This is the existing M3 ingestion preflight. It is intentionally reached
# only after explicit live authorization and the local budget gate.
bash "$ROOT/bin/preflight.sh"

if [[ -e "$ROOT/control/STOP" || -L "$ROOT/control/STOP" ]]; then
    echo "control/STOP appeared during preflight; refusing to start" >&2
    exit 1
fi

if ! PRIME_AGENT_BIN="$(command -v prime-agent)"; then
    echo "prime-agent is not available in PATH; refusing to start" >&2
    exit 1
fi

cd -- "$ROOT"
exec "$PRIME_AGENT_BIN" --skill article-loop --prompt-template "$TEMPLATE"
