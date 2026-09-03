# -*- mode: python ; coding: utf-8 -*-
# ATENCION: este spec vive en INSTALL/. PyInstaller hace os.chdir() a la
# carpeta donde está el spec antes de ejecutarlo, por lo que las rutas
# relativas (fox.py, ICON/) se resolverían contra INSTALL/ y romperían.
# Por eso todas las rutas del proyecto se construyen contra ROOT, deducida
# de la ubicación de este archivo (SPECPATH). No usar rutas relativas sueltas.
import os
import sys

# SPECPATH = carpeta de este archivo (INSTALL/). ROOT = su carpeta padre.
ROOT = os.path.abspath(os.path.join(SPECPATH, os.pardir))


a = Analysis(
    [os.path.join(ROOT, 'SOURCE', 'fox.py')],
    pathex=[os.path.join(ROOT, 'SOURCE')],
    binaries=[],
    datas=[],
    hiddenimports=['scraper', 'requests', 'bs4', 'pdfplumber', 'pdfminer'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='FoxCapital',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=[os.path.join(ROOT, 'ICON', 'fox.ico')] if sys.platform == 'win32' else [],
)
