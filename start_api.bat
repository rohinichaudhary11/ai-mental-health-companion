@echo off
echo Starting Mental Health Companion API Server...
echo.
cd /d "%~dp0"
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000
pause







