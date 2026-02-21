Param(
    [int]$Port = 8000
)

$ErrorActionPreference = 'Stop'

Write-Host '[run_local] Iniciando setup local...' -ForegroundColor Cyan

if (-not (Test-Path '.venv')) {
    Write-Host '[run_local] Creando entorno virtual .venv' -ForegroundColor Yellow
    py -3.11 -m venv .venv
}

$python = Join-Path (Resolve-Path '.venv').Path 'Scripts\python.exe'
$activate = Join-Path (Resolve-Path '.venv').Path 'Scripts\Activate.ps1'

. $activate

Write-Host '[run_local] Actualizando pip e instalando dependencias...' -ForegroundColor Cyan
& $python -m pip install --upgrade pip
& $python -m pip install -r requirements.txt

if (-not (Test-Path '.env')) {
    Copy-Item .env.example .env
    Write-Host '[run_local] Se creó .env desde .env.example (revisá OPENAI_API_KEY si querés IA).' -ForegroundColor Yellow
}

$dbPath = ''
Get-Content '.env' | ForEach-Object {
    if ($_ -match '^\s*DB_PATH\s*=\s*(.+)\s*$') {
        $dbPath = $Matches[1].Trim()
    }
}
if (-not $dbPath) {
    $dbPath = 'data/indoor.db'
}

$dbDir = Split-Path -Parent $dbPath
if (-not [string]::IsNullOrWhiteSpace($dbDir) -and -not (Test-Path $dbDir)) {
    New-Item -ItemType Directory -Path $dbDir | Out-Null
    Write-Host "[run_local] Carpeta creada: $dbDir" -ForegroundColor Yellow
}

Write-Host '[run_local] Inicializando DB...' -ForegroundColor Cyan
& $python scripts\init_db.py

Write-Host '[run_local] Insertando/actualizando seed demo...' -ForegroundColor Cyan
& $python scripts\seed_demo.py

Write-Host "[run_local] Levantando API en http://127.0.0.1:$Port" -ForegroundColor Green
& $python -m uvicorn app.main:app --reload --host 127.0.0.1 --port $Port
