@echo off
echo [SYSTEM] Activating Virtual Environment...
call venv\Scripts\activate

echo [SYSTEM] Cleaning up ghost processes...
powershell -ExecutionPolicy Bypass -File .\cleanup.ps1

echo [SYSTEM] Starting AI Surveillance System...
python run_system.py

pause
