@echo off
echo ========================================
echo Mental Health Companion - Starting Services
echo ========================================
echo.

cd /d "%~dp0"

echo Starting API Server in new window...
start "Mental Health Companion API" cmd /k "python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000"

echo Waiting for API to start...
timeout /t 5 /nobreak >nul

echo Starting Frontend in new window...
start "Mental Health Companion Frontend" cmd /k "streamlit run src/frontend/app.py"

echo.
echo ========================================
echo Services Started!
echo ========================================
echo.
echo API Server: http://localhost:8000
echo API Docs:   http://localhost:8000/docs
echo Frontend:   http://localhost:8501
echo.
echo Both services are running in separate windows.
echo Close those windows to stop the services.
echo.
pause







