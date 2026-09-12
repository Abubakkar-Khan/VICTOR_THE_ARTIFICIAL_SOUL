@echo off
title Dexter — The Artificial Soul Builder
python builder.py %*
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Build encountered errors.
    pause
    exit /b %errorlevel%
)
