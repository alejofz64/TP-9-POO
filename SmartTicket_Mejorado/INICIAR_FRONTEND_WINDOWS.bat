@echo off
setlocal
cd /d "%~dp0frontend"
where npm >nul 2>nul
if errorlevel 1 (
  echo Node.js y npm no estan instalados. Instalar Node.js LTS desde https://nodejs.org/
  pause
  exit /b 1
)
if not exist node_modules (
  echo Instalando dependencias del frontend...
  call npm install
  if errorlevel 1 (
    echo Error al instalar las dependencias.
    pause
    exit /b 1
  )
)
echo Abri: http://127.0.0.1:5173
call npm run dev
pause
