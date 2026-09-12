@echo off
title Dexter — The Artificial Soul
echo ========================================
echo   Dexter — The Artificial Soul
echo ========================================

netstat -ano | findstr :8000 | findstr LISTENING >nul 2>&1
if %errorlevel% neq 0 (
    echo [1/3] Starting Dexter API server on port 8000...
    start /b "" python -m dexter.api.server
    timeout /t 2 /nobreak >nul
) else (
    echo [1/3] Dexter API server is already active on port 8000.
)

echo [2/3] Opening Dexter Workshop in default browser...
start http://localhost:8000

echo [3/3] Launching Dexter Desktop Mascot...
start "" python -m dexter.desktop.mascot

echo.
echo Dexter is running!
echo • Workshop: http://localhost:8000
echo • Desktop Mascot: check bottom-right of your screen
echo.
