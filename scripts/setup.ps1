# Crea el entorno virtual .venv e instala las dependencias del proyecto.
#
# Uso, desde la raíz del repositorio:
#   powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
#   powershell -ExecutionPolicy Bypass -File scripts\setup.ps1 -Version 3.12   # fuerza una versión de Python
param(
    [string]$Version = "3"
)
$ErrorActionPreference = "Stop"
$raiz = Split-Path -Parent $PSScriptRoot
Set-Location $raiz

# 1. Buscar Python: lanzador "py" de Windows o, si no existe, "python"
if (Get-Command py -ErrorAction SilentlyContinue) {
    $exe = "py"; $pre = @("-$Version")
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $exe = "python"; $pre = @()
} else {
    throw "No se encontró Python. Instala Python 3.12 desde python.org y marca 'Add python.exe to PATH'."
}

& $exe @pre -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)"
if ($LASTEXITCODE -ne 0) { throw "Se requiere Python 3.10 o superior (recomendado 3.12)." }
& $exe @pre --version

# 2. Crear .venv (si ya existe, se reutiliza)
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "Creando entorno virtual .venv ..."
    & $exe @pre -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw "No se pudo crear .venv" }
} else {
    Write-Host ".venv ya existe: se reutiliza."
}

# 3. Instalar dependencias con el Python del entorno (no hace falta activarlo)
$venvPy = Join-Path $raiz ".venv\Scripts\python.exe"
& $venvPy -m pip install --upgrade pip
& $venvPy -m pip install --no-warn-script-location -r requirements-dev.txt
if ($LASTEXITCODE -ne 0) { throw "Falló la instalación de dependencias." }

# 4. Registrar el entorno como kernel de Jupyter para el notebook
& $venvPy -m ipykernel install --user --name streamview --display-name "Python (StreamView .venv)"

Write-Host ""
Write-Host "Entorno listo." -ForegroundColor Green
Write-Host "  Activar:        .\.venv\Scripts\Activate.ps1"
Write-Host "  Correr la app:  streamlit run app.py"
