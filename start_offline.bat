@echo off
REM Sahaay - offline presentation launcher (Windows)
REM Run ONCE while online first (installs Python packages); afterwards works with no internet.
cd /d "%~dp0backend"

if not exist .venv (
  echo First run: creating Python environment and installing packages ^(needs internet once^)...
  python -m venv .venv
  .venv\Scripts\pip install -r requirements.txt
)

.venv\Scripts\python seed.py
echo.
echo Sahaay is starting at  http://localhost:8001  (close this window to stop)
start "" http://localhost:8001
.venv\Scripts\python server.py
