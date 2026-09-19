@echo off
setlocal
cd /d "%~dp0frontend"

if not exist "package-lock.json" (
  echo [HATA] frontend/package-lock.json bulunamadi.
  exit /b 1
)

if not exist "node_modules\next\package.json" (
  echo Frontend bagimliliklari kuruluyor...
  call npm ci
  if errorlevel 1 (
    echo [HATA] npm ci basarisiz.
    exit /b 1
  )
)

call npm run dev
