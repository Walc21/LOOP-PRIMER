#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
exec "$ROOT/.venv/bin/python" -c 'import sys; from pathlib import Path; sys.path.insert(0, str(Path(sys.argv[1]) / ".prime/agent/skills/article-loop/src")); from article_loop import ingest; result = ingest(sys.argv[1]); print("{}: {} ({})".format(result["status"], result["champion"], result["sha256"]))' "$ROOT"
