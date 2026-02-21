@echo off
setlocal

if not exist .venv\Scripts\python.exe (
  echo [ERROR] No se encontro .venv\. Crea el entorno virtual primero con:
  echo         py -3.11 -m venv .venv
  exit /b 1
)

call .venv\Scripts\activate.bat
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

endlocal
