@echo off
title Mental Health Companion - Starting Services
color 0A

echo ========================================
echo   AI-Powered Mental Health Companion
echo   Starting Complete Application
echo ========================================
echo.

cd /d "%~dp0"

echo [1/4] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)
echo       Python found!

echo.
echo [2/4] Checking dependencies...
python -c "import fastapi, streamlit, transformers, plotly" >nul 2>&1
if errorlevel 1 (
    echo       Installing missing dependencies...
    pip install -q fastapi uvicorn streamlit transformers torch plotly pandas requests
) else (
    echo       All dependencies installed!
)

echo.
echo [3/4] Starting API Server...
start "Mental Health Companion - API Server" cmd /k "cd /d %~dp0 && echo === API Server === && echo Starting on http://0.0.0.0:8000 && echo. && python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000"

echo       Waiting for API to start...
timeout /t 8 /nobreak >nul

echo.
echo [4/4] Starting Frontend...
start "Mental Health Companion - Frontend" cmd /k "cd /d %~dp0 && echo === Frontend Server === && echo Starting on http://localhost:8501 && echo. && streamlit run src/frontend/app.py --server.port 8501"

echo       Waiting for Frontend to start...
timeout /t 10 /nobreak >nul

echo.
echo ========================================
echo   Services Started!
echo ========================================
echo.
echo   API Server:  http://localhost:8000
echo   API Docs:    http://localhost:8000/docs
echo   Frontend:    http://localhost:8501
echo.
echo   Opening browser...
echo.
timeout /t 2 /nobreak >nul
start http://localhost:8501

echo ========================================
echo   Application is ready!
echo ========================================
echo.
echo   Two windows have opened:
echo   - API Server window (keep open)
echo   - Frontend window (keep open)
echo.
echo   Close those windows to stop the services.
echo.
pause







