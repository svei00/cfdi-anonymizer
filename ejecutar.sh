#!/usr/bin/env bash
# ============================================================
#  CFDI Anonymizer - lanzador para Linux / macOS
#  Uso:  chmod +x ejecutar.sh   y luego  ./ejecutar.sh
#  (o doble clic si tu entorno de escritorio lo permite)
# ============================================================
set -e
cd "$(dirname "$0")"

# Detectar interprete de Python 3
if command -v python3 >/dev/null 2>&1; then
    PY=python3
elif command -v python >/dev/null 2>&1; then
    PY=python
else
    echo "No se encontro Python 3. Instalalo con tu gestor de paquetes."
    exit 1
fi

# Verificar Tkinter (en Linux suele requerir el paquete python3-tk)
if ! "$PY" -c "import tkinter" >/dev/null 2>&1; then
    echo "Falta Tkinter. En Debian/Ubuntu:  sudo apt install python3-tk"
    echo "En Fedora:  sudo dnf install python3-tkinter"
    exit 1
fi

# Instalar dependencias solo si falta lxml
if ! "$PY" -c "import lxml" >/dev/null 2>&1; then
    echo "Instalando dependencias por primera vez..."
    "$PY" -m pip install -r requirements.txt
fi

exec "$PY" main.py
