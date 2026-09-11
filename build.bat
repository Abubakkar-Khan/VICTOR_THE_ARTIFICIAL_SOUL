@echo off
title Build & Verify Victor
echo ===================================================
echo   Building and Verifying Victor — The Artificial Soul
echo ===================================================

echo.
echo [1/2] Checking dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies.
    exit /b %errorlevel%
)

echo.
echo [2/2] Running test suite...
python -m pytest -v tests/
if %errorlevel% neq 0 (
    echo [ERROR] Test suite failed!
    exit /b %errorlevel%
)

echo.
echo ===================================================
echo   Build verification complete! All tests passed.
echo   To start Victor, run: run.bat
echo ===================================================
