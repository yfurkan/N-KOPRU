@echo off
setlocal
cd /d "%~dp0backend"
if not exist ".venv\Scripts\python.exe" (
  echo [HATA] Once backend sanal ortamini olusturun.
  pause
  exit /b 1
)
call .venv\Scripts\activate.bat
python -m pip install -r requirements-ai.txt
if errorlevel 1 (
  echo.
  echo [HATA] AI paketleri kurulurken hata olustu.
  pause
  exit /b 1
)
echo.
echo AI paketleri kuruldu. Backend'i yeniden baslatin ve arayuzde AI Modelini Hazirla'ya basin.
pause
