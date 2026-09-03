@echo off
rem Este script vive en INSTALL/: movemos a la raiz del proyecto (%~dp0..)
rem para que build.py (en SOURCE/) y sus rutas resuelvan correctamente.
cd /d "%~dp0.."

echo =============================================
echo   FoxCapital - build (Windows)
echo =============================================

python SOURCE\build.py
if errorlevel 1 (
    echo.
    echo Build fallo. Revisa los errores de arriba.
    pause
    exit /b 1
)

echo.
echo Listo! Ejecutable en FoxCapital.exe
pause
