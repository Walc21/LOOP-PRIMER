#!/bin/sh
# Prepare the canonical local CPython 3.14 environment. Never starts Prime or a model.
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd -P)

if [ ! -r /etc/os-release ]; then
    echo "Sistema não suportado: este bootstrap requer Debian ou Ubuntu." >&2
    exit 1
fi

. /etc/os-release
case "${ID:-} ${ID_LIKE:-}" in
    debian*|ubuntu*|*' debian '*|*' ubuntu '*) ;;
    *)
        echo "Sistema não suportado: use Debian ou Ubuntu, ou instale os requisitos manualmente." >&2
        exit 1
        ;;
esac

if [ -L "$ROOT/.python-version" ] || [ ! -f "$ROOT/.python-version" ] || [ "$(cat "$ROOT/.python-version")" != "3.14" ]; then
    echo "Este checkout exige .python-version = 3.14." >&2
    exit 1
fi
if [ -L "$ROOT/.venv" ]; then
    echo "A .venv não pode ser link simbólico. Remova-a e execute: bash bin/bootstrap-deps.sh" >&2
    exit 1
fi
if [ -e "$ROOT/.venv" ] && [ ! -d "$ROOT/.venv" ]; then
    echo "A .venv existente não é um diretório. Remova-a e execute: bash bin/bootstrap-deps.sh" >&2
    exit 1
fi
VENV_EXISTS=0
if [ -d "$ROOT/.venv" ]; then
    VENV_EXISTS=1
    if [ ! -x "$ROOT/.venv/bin/python" ] || [ ! -f "$ROOT/.venv/pyvenv.cfg" ]; then
        echo "A .venv está quebrada. Remova-a e execute: bash bin/bootstrap-deps.sh" >&2
        exit 1
    fi
    if ! "$ROOT/.venv/bin/python" - "$ROOT" <<'PY'
from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve()
expected = (root / ".venv").resolve()
config = expected / "pyvenv.cfg"
values = {}
for line in config.read_text(encoding="utf-8").splitlines():
    if "=" in line:
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
try:
    command = values["command"]
except KeyError:
    raise SystemExit(1)
valid = (
    sys.implementation.name == "cpython"
    and sys.version_info[:2] == (3, 14)
    and Path(sys.prefix).resolve() == expected
    and Path(sys.base_prefix).resolve() != expected
    and " -m venv " in command
    and command.endswith(" " + str(expected))
)
raise SystemExit(0 if valid else 1)
PY
    then
        echo "A .venv foi movida, está quebrada ou usa outra versão. Remova-a e execute: bash bin/bootstrap-deps.sh" >&2
        exit 1
    fi
fi

PYTHON314=''
if [ "$VENV_EXISTS" -eq 0 ]; then
    if ! PYTHON314=$(command -v python3.14); then
        echo "CPython 3.14 não está disponível em PATH; instale-o e execute novamente." >&2
        exit 1
    fi
    if ! "$PYTHON314" -c 'import sys; raise SystemExit(0 if sys.implementation.name == "cpython" and sys.version_info[:2] == (3, 14) else 1)'; then
        echo "python3.14 não é um CPython 3.14 válido." >&2
        exit 1
    fi
fi

packages=''
need_package() {
    if ! command -v "$1" >/dev/null 2>&1; then
        packages="$packages $2"
    fi
}

if [ "$VENV_EXISTS" -eq 0 ] && ! "$PYTHON314" -m venv --help >/dev/null 2>&1; then
    packages="$packages python3.14-venv"
fi
need_package pdfinfo poppler-utils
need_package pdftotext poppler-utils
need_package pdftoppm poppler-utils
need_package pdfimages poppler-utils
need_package pdflatex texlive-latex-base

if [ -n "$packages" ]; then
    if [ "$(id -u)" -eq 0 ]; then
        SUDO=''
    elif command -v sudo >/dev/null 2>&1; then
        SUDO=sudo
    else
        echo "São necessários privilégios administrativos para instalar:$packages" >&2
        exit 1
    fi
    echo "Instalando pacotes de sistema ausentes:$packages"
    $SUDO apt-get update
    # A lista pode conter duplicatas; o apt trata isso de forma idempotente.
    $SUDO apt-get install -y $packages
fi

if [ "$VENV_EXISTS" -eq 0 ]; then
    "$PYTHON314" -m venv "$ROOT/.venv"
fi

"$ROOT/bin/python-runtime.sh" "$ROOT"
"$ROOT/.venv/bin/python" -m pip install --disable-pip-version-check -r "$ROOT/requirements-dev.txt"
echo "Ambiente CPython 3.14 pronto. Verifique com: $ROOT/.venv/bin/python -m unittest -v control.test_contracts"
