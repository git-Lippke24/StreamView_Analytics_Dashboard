#!/usr/bin/env bash
# Crea el entorno virtual .venv e instala las dependencias (Mac / Linux).
# Uso, desde la raíz del repositorio:  bash scripts/setup.sh
# Otra versión de Python:              PYTHON=python3.12 bash scripts/setup.sh
set -euo pipefail
cd "$(dirname "$0")/.."

PY="${PYTHON:-python3}"
"$PY" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' \
  || { echo "Se requiere Python 3.10 o superior (recomendado 3.12)."; exit 1; }
"$PY" --version

if [ ! -x .venv/bin/python ]; then
  echo "Creando entorno virtual .venv ..."
  "$PY" -m venv .venv
else
  echo ".venv ya existe: se reutiliza."
fi

.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install --no-warn-script-location -r requirements-dev.txt
.venv/bin/python -m ipykernel install --user --name streamview --display-name "Python (StreamView .venv)"

echo ""
echo "Entorno listo."
echo "  Activar:        source .venv/bin/activate"
echo "  Correr la app:  streamlit run app.py"
