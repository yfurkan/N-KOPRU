@echo off
setlocal
cd /d "%~dp0backend"

if not exist ".venv\Scripts\python.exe" (
  echo [HATA] Backend sanal ortami bulunamadi.
  echo Once README.md icindeki kurulum adimlariyla .venv olusturun.
  exit /b 1
)

call .venv\Scripts\activate.bat
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
