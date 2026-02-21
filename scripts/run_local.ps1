Param(
    [int]$Port = 8000
)

$ErrorActionPreference = 'Stop'

function Exit-WithError {
    param(
        [string]$Message,
        [int]$Code = 1
    )
    Write-Host "[run_local][ERROR] $Message" -ForegroundColor Red
    exit $Code
}

function Get-PythonLauncherCommand {
    if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
        Exit-WithError "No se encontró el Python Launcher ('py'). Instalá Python desde python.org habilitando el launcher."
    }

    $candidates = @(
        @{ Label = 'py -3.12'; Args = @('-3.12') },
        @{ Label = 'py -3.11'; Args = @('-3.11') },
        @{ Label = 'py'; Args = @() }
    )

    foreach ($candidate in $candidates) {
        try {
            & py @($candidate.Args + @('-c', 'import sys')) | Out-Null
            if ($LASTEXITCODE -eq 0) {
                return $candidate
            }
        }
        catch {
            continue
        }
    }

    Exit-WithError "No se pudo ejecutar Python con 'py -3.12', 'py -3.11' ni 'py'."
}

try {
    Write-Host '[run_local] Iniciando setup local...' -ForegroundColor Cyan

    $pyCommand = Get-PythonLauncherCommand
    Write-Host "[run_local] Usando Python: $($pyCommand.Label)" -ForegroundColor Cyan

    $venvPath = Join-Path $PWD.Path '.venv'
    $python = Join-Path $PWD.Path '.venv\Scripts\python.exe'

    if (-not (Test-Path $venvPath)) {
        Write-Host '[run_local] Creando entorno virtual .venv' -ForegroundColor Yellow
        & py @($pyCommand.Args + @('-m', 'venv', '.venv'))
        if ($LASTEXITCODE -ne 0) {
            Exit-WithError "Falló la creación de .venv con $($pyCommand.Label)."
        }
    }
    else {
        Write-Host '[run_local] .venv ya existe, se reutiliza.' -ForegroundColor Yellow
    }

    if (-not (Test-Path $python)) {
        Exit-WithError "No se encontró $python luego de crear/reusar .venv."
    }

    Write-Host '[run_local] Actualizando pip e instalando dependencias...' -ForegroundColor Cyan
    & $python -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) {
        Exit-WithError 'Falló actualización de pip.'
    }
    & $python -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Exit-WithError 'Falló instalación de requirements.txt.'
    }

    if (-not (Test-Path '.env')) {
        Copy-Item '.env.example' '.env'
        Write-Host '[run_local] Se creó .env desde .env.example (revisá OPENAI_API_KEY si querés IA).' -ForegroundColor Yellow
    }
    else {
        Write-Host '[run_local] .env ya existe, no se sobrescribe.' -ForegroundColor Yellow
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
    & $python 'scripts\init_db.py'
    if ($LASTEXITCODE -ne 0) {
        Exit-WithError 'Falló scripts/init_db.py.'
    }

    Write-Host '[run_local] Insertando/actualizando seed demo...' -ForegroundColor Cyan
    & $python 'scripts\seed_demo.py'
    if ($LASTEXITCODE -ne 0) {
        Exit-WithError 'Falló scripts/seed_demo.py.'
    }

    Write-Host "[run_local] Levantando API en http://127.0.0.1:$Port" -ForegroundColor Green
    & $python -m uvicorn app.main:app --reload --host 127.0.0.1 --port $Port
    if ($LASTEXITCODE -ne 0) {
        Exit-WithError 'Falló el arranque de uvicorn.'
    }
}
catch {
    Exit-WithError $_.Exception.Message
}
