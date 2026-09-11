@echo off
title Victor — The Artificial Soul
echo ========================================
echo   Victor — The Artificial Soul
echo ========================================

netstat -ano | findstr :8000 | findstr LISTENING >nul 2>&1
if %errorlevel% neq 0 (
    echo [1/3] Starting Victor API server on port 8000...
    start /b "" python -m victor.api.server
    timeout /t 2 /nobreak >nul
) else (
    echo [1/3] Victor API server is already active on port 8000.
)

echo [2/3] Opening Victor Workshop in default browser...
start http://localhost:8000

echo [3/3] Launching Victor Desktop Mascot...
start "" python -m victor.desktop.mascot

echo.
echo Victor is running!
echo • Workshop: http://localhost:8000
echo • Desktop Mascot: check bottom-right of your screen
echo.
