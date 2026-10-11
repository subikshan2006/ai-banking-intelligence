@echo off
TITLE Banking AI Platform - Production Launcher
echo ====================================================================
echo             AI BANKING INTELLIGENCE PLATFORM
echo       Autonomous Multi-Agent Enterprise Architecture
echo ====================================================================
echo.

cd /d "%~dp0"

echo [1/3] Verifying and Initializing Banking Database...
python scripts/reset_demo.py
if errorlevel 1 (
    echo [ERROR] Database initialization failed. Exiting.
    pause
    exit /b 1
)

echo.
echo [2/3] Launching FastAPI Backend Server (Port 8000)...
start "Banking AI Backend" cmd /k "cd backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

echo.
echo [3/3] Launching React Frontend Application (Port 5173)...
start "Banking AI Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ====================================================================
echo  System startup initiated!
echo  Backend API Docs : http://localhost:8000/docs
echo  Frontend App UI  : http://localhost:5173
echo ====================================================================
echo.
timeout /t 5 >nul
start http://localhost:5173

pause
