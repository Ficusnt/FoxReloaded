#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build.py — Compila FoxCapital con PyInstaller usando FoxCapital.spec.

OS-agnóstico: detecta dónde se ejecuta y genera el ejecutable correcto.
    - Windows:  FoxCapital.exe   (con icono ICON/fox.ico)
    - Linux:    FoxCapital       (ELF, sin icono)

El ejecutable final queda en la raíz del proyecto; build/ y dist/ se
borran (son intermedios). En debug/ se guarda warn-FoxCapital.txt con
los avisos de dependencias de PyInstaller.

Uso:
    python build.py
"""
import os
import shutil
import subprocess
import sys
import time

# build.py vive en SOURCE/; la raíz del proyecto es su carpeta padre.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = os.path.join(ROOT, "INSTALL", "FoxCapital.spec")
DEBUG_DIR = os.path.join(ROOT, "debug")
IS_WIN = os.name == "nt"
OUT_NAME = "FoxCapital.exe" if IS_WIN else "FoxCapital"


def _rmtree(folder):
    """Borra un directorio; reintenta ante bloqueos transitorios (Windows:
    Explorer/antivirus a veces retienen el folder por unos instantes)."""
    if not os.path.isdir(folder):
        return
    print(f"  limpiando {os.path.basename(folder)}/")
    for attempt in range(4):
        try:
            shutil.rmtree(folder)
            return
        except OSError as exc:
            if attempt == 3:
                # Bloqueo persistente (antivirus, un exe abierto): avisamos y seguimos.
                print(f"  (aviso) no se pudo limpiar {folder}: {exc}")
            else:
                time.sleep(0.4)


def main():
    print("=" * 60)
    print(f"  FoxCapital build ({'Windows' if IS_WIN else 'Linux'})")
    print("=" * 60)

    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("ERROR: no se encontró PyInstaller. Instalá las dependencias:")
        print("  Windows:  python -m pip install -r requirements.txt")
        print("  Linux:    ./install.sh   (crea/usa .venv e instala)")
        sys.exit(1)

    # Limpieza previa para una build reproducible
    for folder in ("build", "dist"):
        _rmtree(os.path.join(ROOT, folder))
    _rmtree(DEBUG_DIR)
    root_exe = os.path.join(ROOT, OUT_NAME)
    if os.path.isfile(root_exe):
        print(f"  removiendo {OUT_NAME}")
        try:
            os.remove(root_exe)
        except OSError as exc:
            print(f"  (aviso) no se pudo remover {OUT_NAME}: {exc}")

    cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", SPEC]
    print("  compilando con PyInstaller...")
    ret = subprocess.run(cmd, cwd=ROOT)
    if ret.returncode != 0:
        # Dejamos build/ y dist/ para poder depurar (warn-*.txt, xref).
        print("ERROR: falló la compilación. Se conservó build/ para depurar.")
        sys.exit(ret.returncode)

    built = os.path.join(ROOT, "dist", OUT_NAME)
    if not os.path.isfile(built):
        print("ERROR: no se generó el ejecutable en dist/.")
        sys.exit(1)

    # 1) Mover el ejecutable a la raíz
    print(f"  moviendo {OUT_NAME} a la raíz")
    try:
        os.replace(built, root_exe)
    except OSError as exc:
        print(f"ERROR: no se pudo mover el ejecutable: {exc}")
        sys.exit(1)

    # 2) Guardar los avisos de dependencias en debug/
    try:
        warn_src = os.path.join(ROOT, "build", "FoxCapital",
                                "warn-FoxCapital.txt")
        if os.path.isfile(warn_src):
            os.makedirs(DEBUG_DIR, exist_ok=True)
            shutil.copy2(warn_src, os.path.join(DEBUG_DIR, "warn-FoxCapital.txt"))
            print("  avisos de PyInstaller guardados en debug/warn-FoxCapital.txt")
        else:
            print("  (aviso) no se encontró warn-FoxCapital.txt de PyInstaller")
    except OSError as exc:
        print(f"  (aviso) no se pudo guardar el warn: {exc}")

    # 3) Borrar intermedios (build/ y dist/)
    _rmtree(os.path.join(ROOT, "build"))
    _rmtree(os.path.join(ROOT, "dist"))

    print("-" * 60)
    print("  Build OK!")
    print(f"  Ejecutable: {root_exe}")
    print("-" * 60)


if __name__ == "__main__":
    main()
