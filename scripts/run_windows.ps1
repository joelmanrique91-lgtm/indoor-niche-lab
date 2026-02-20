Param(
    [switch]$SkipSeed,
    [int]$Port = 8000
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path '.venv')) {
    py -m venv .venv
}

$python = Join-Path (Resolve-Path '.venv').Path 'Scripts\python.exe'
$pip = Join-Path (Resolve-Path '.venv').Path 'Scripts\pip.exe'

& $pip install -r requirements.txt

if (-not (Test-Path '.env')) {
    Copy-Item .env.example .env
    Write-Host 'Se creó .env desde .env.example. Revisá OPENAI_API_KEY antes de usar generación IA.'
}

& $python scripts\init_db.py

if (-not $SkipSeed) {
    & $python scripts\seed_demo.py
}

& $python -m uvicorn app.main:app --reload --host 127.0.0.1 --port $Port
