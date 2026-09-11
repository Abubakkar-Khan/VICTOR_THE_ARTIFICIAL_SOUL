@echo off
title Build & Package Victor — The Artificial Soul
echo ===================================================
echo   Building & Packaging Victor — The Artificial Soul
echo ===================================================

echo.
echo [1/3] Checking dependencies...
pip install -r requirements.txt pyinstaller
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies.
    exit /b %errorlevel%
)

echo.
echo [2/3] Running test suite...
python -m pytest -v tests/
if %errorlevel% neq 0 (
    echo [ERROR] Test suite failed!
    exit /b %errorlevel%
)

echo.
echo [3/3] Compiling standalone desktop executable with PyInstaller...
pyinstaller --noconfirm --clean victor.spec
if %errorlevel% neq 0 (
    echo [ERROR] PyInstaller compilation failed!
    exit /b %errorlevel%
)

echo.
echo ===================================================
echo   BUILD COMPLETE!
echo   Standalone application built: dist\Victor\Victor.exe
echo ===================================================
