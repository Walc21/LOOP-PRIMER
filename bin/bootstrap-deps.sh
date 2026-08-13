#!/bin/sh
# Prepara requisitos locais da ingestão M3. Não instala nem inicia o Prime Agent.
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)

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

packages=''
need_package() {
    if ! command -v "$1" >/dev/null 2>&1; then
        packages="$packages $2"
    fi
}

need_package python3 python3
if ! python3 -m venv --help >/dev/null 2>&1; then
    packages="$packages python3-venv"
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

if ! python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)'; then
    echo "Python 3.11 ou superior é necessário; a versão disponível é: $(python3 --version)" >&2
    exit 1
fi

if [ -L "$ROOT/.venv" ]; then
    echo "Recusando usar .venv como link simbólico; remova-o ou crie um diretório local." >&2
    exit 1
fi
if [ ! -e "$ROOT/.venv" ]; then
    python3 -m venv "$ROOT/.venv"
fi

"$ROOT/.venv/bin/python" -m pip install --disable-pip-version-check -r "$ROOT/requirements-dev.txt"
echo "Ambiente pronto. Verifique com: $ROOT/.venv/bin/python -m unittest -v control.test_contracts"
