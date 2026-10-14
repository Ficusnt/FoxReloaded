#!/bin/bash
# FoxCapital - build (Linux).
# Crea/usa un venv (.venv) e instala las dependencias, luego compila con
# build.py. Pensado para Bazzite/WSL: en distros "externally-managed"
# (PEP 668) el pip global esta bloqueado, por eso usamos un entorno virtual.
# Uso:
#   ./install.sh           # primer build (instala deps en .venv)
#   ./install.sh --fresh   # fuerza reinstalacion de dependencias
set -e

# Este script vive en INSTALL/, asi que la raiz del proyecto es su carpeta
# padre (los assets, venv, requirements.txt y build.py estan en la raiz).
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV="$ROOT/.venv"
REQ="$ROOT/requirements.txt"
Vpy="$VENV/bin/python"
PY="python3"

echo "==============================================="
echo "  FoxCapital - build (Linux)"
echo "==============================================="

# 1) python3, venv/ensurepip, y tkinter disponibles
if ! command -v "$PY" &> /dev/null; then
    echo "ERROR: python3 no esta instalado."
    exit 1
fi
if ! "$PY" -c "import venv, ensurepip" &> /dev/null; then
    echo "ERROR: falta venv/ensurepip para crear entornos virtuales."
    echo "  En Debian/Ubuntu/Q4OS (una sola vez):"
    echo "    sudo apt update && sudo apt install -y python3-venv"
    echo "  (el nombre exacto del paquete depende de tu Python;"
    echo "   por ejemplo python3.14-venv). Luego reintentá ./install.sh"
    exit 1
fi
if ! "$PY" -c "import tkinter" &> /dev/null; then
    # Detectar distro y ofrecer paquete apropiado
    PKG=""
    CMD=""
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        case "$ID" in
            debian|ubuntu|q4os|linuxmint|pop|elementary|zorin|neon)
                PKG="python3-tk"
                CMD="sudo apt update && sudo apt install -y $PKG"
                ;;
            fedora|rhel|centos|rocky|almalinux)
                PKG="python3-tkinter"
                CMD="sudo dnf install -y $PKG"
                ;;
            arch|manjaro|endeavouros|garuda)
                PKG="tk"
                CMD="sudo pacman -S --noconfirm $PKG"
                ;;
            opensuse*|suse*)
                PKG="python3-tk"
                CMD="sudo zypper install -y $PKG"
                ;;
            alpine)
                PKG="python3-tkinter"
                CMD="sudo apk add $PKG"
                ;;
            *)
                PKG="(desconocido)"
                CMD=""
                ;;
        esac
    fi
    
    echo "ERROR: falta tkinter (GUI no funcionara)."
    if [ -n "$CMD" ]; then
        echo "  Distro detectada: $PRETTY_NAME"
        echo "  Paquete: $PKG"
        echo "  Comando: $CMD"
        read -p "¿Instalar automaticamente con sudo? [s/N] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Ss]$ ]]; then
            eval "$CMD"
            # Verificar que se instalo
            if "$PY" -c "import tkinter" &> /dev/null; then
                echo "  tkinter instalado correctamente."
            else
                echo "  Fallo la instalacion. Ejecuta manualmente: $CMD"
                exit 1
            fi
        else
            echo "  Instala $PKG y reintentá ./install.sh"
            exit 1
        fi
    else
        echo "  No se pudo detectar la distro automaticamente."
        echo "  Instala tkinter para tu distribucion y reintentá ./install.sh"
        exit 1
    fi
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

# 4) Compilacion (build.py detecta el SO y deja FoxCapital en la raiz)
echo ""
echo "  compilando con build.py..."
"$Vpy" "$ROOT/SOURCE/build.py"

echo ""
echo "  Listo! Ejecutable en FoxCapital"
echo "  (avisos de PyInstaller en debug/warn-FoxCapital.txt)"
echo "==============================================="