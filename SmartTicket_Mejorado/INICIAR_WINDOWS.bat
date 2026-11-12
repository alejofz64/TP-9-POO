@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  echo Creando entorno virtual...
  py -m venv .venv
)
echo Instalando dependencias si hace falta...
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 (
  echo Error al instalar dependencias.
  pause
  exit /b 1
)
echo Preparando datos de demo...
.venv\Scripts\python.exe seed_demo.py
if errorlevel 1 (
  pause
  exit /b 1
)
echo.
echo Abrir: http://127.0.0.1:8000/docs
.venv\Scripts\python.exe -m uvicorn app.main:app --reload
pause
