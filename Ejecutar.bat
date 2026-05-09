@echo off
REM ============================================================
REM  CFDI Anonymizer - lanzador para Windows (doble clic)
REM ============================================================
chcp 65001 >nul
cd /d "%~dp0"

REM Detectar lanzador de Python (py preferido, luego python)
where py >nul 2>nul && (set "PY=py") || (set "PY=python")

REM Verificar que Python exista
%PY% --version >nul 2>nul
if errorlevel 1 (
    echo No se encontro Python. Instalalo desde https://www.python.org/downloads/
    echo Marca "Add Python to PATH" durante la instalacion.
    pause
    exit /b 1
)

REM Instalar dependencias solo si falta lxml
%PY% -c "import lxml" >nul 2>nul || (
    echo Instalando dependencias por primera vez...
    %PY% -m pip install -r requirements.txt
)

REM Lanzar la interfaz grafica
%PY% main.py
if errorlevel 1 (
    echo.
    echo Ocurrio un error. Revisa el mensaje de arriba.
    pause
)
