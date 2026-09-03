#!/bin/bash
# FoxCapital - build (Linux).
# Crea/usa un venv (.venv) e instala las dependencias, luego compila con
# build.py. Pensado para Bazzite/WSL: en distros "externally-managed"
# (PEP 668) el pip global está bloqueado, por eso usamos un entorno virtual.
# Uso:
#   ./install.sh           # primer build (instala deps en .venv)
#   ./install.sh --fresh   # fuerza reinstalación de dependencias
set -e

# Este script vive en INSTALL/, así que la raíz del proyecto es su carpeta
# padre (los assets, venv, requirements.txt y build.py están en la raíz).
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV="$ROOT/.venv"
REQ="$ROOT/requirements.txt"
Vpy="$VENV/bin/python"
PY="python3"

echo "==============================================="
echo "  FoxCapital - build (Linux)"
echo "==============================================="

# 1) python3 y el soporte de venv/ensurepip disponibles
if ! command -v "$PY" &> /dev/null; then
    echo "ERROR: python3 no está instalado."
    exit 1
fi
if ! "$PY" -c "import venv, ensurepip" &> /dev/null; then
    echo "ERROR: falta 'venv'/'ensurepip' para crear entornos virtuales."
    echo "  En Debian/Ubuntu (una sola vez):"
    echo "    sudo apt update && sudo apt install -y python3-venv"
    echo "  (el nombre exacto del paquete depende de tu Python;"
    echo "   por ejemplo python3.14-venv). Luego reintentá ./install.sh"
    exit 1
fi

# 2) Crear el venv (solo la primera vez)
if [ ! -x "$Vpy" ]; then
    echo "  creando venv: $VENV"
    "$PY" -m venv "$VENV"
else
    echo "  usando venv existente: $VENV"
fi

# 3) Instalar dependencias si faltan (o con --fresh)
if [ "$1" = "--fresh" ]; then
    echo "  reinstalando dependencias..."
    "$Vpy" -m pip install --upgrade -r "$REQ"
elif "$Vpy" -c "import PyInstaller" &> /dev/null && \
     "$Vpy" -c "import requests, bs4, pdfplumber, reportlab" &> /dev/null; then
    echo "  dependencias ok (usa --fresh para reinstalarlas)"
else
    echo "  instalando dependencias en el venv..."
    "$Vpy" -m pip install -r "$REQ"
fi

# 4) Compilación (build.py detecta el SO y deja FoxCapital en la raíz)
echo ""
echo "  compilando con build.py..."
"$Vpy" "$ROOT/SOURCE/build.py"

echo ""
echo "  Listo! Ejecutable en FoxCapital"
echo "  (avisos de PyInstaller en debug/warn-FoxCapital.txt)"
echo "==============================================="
