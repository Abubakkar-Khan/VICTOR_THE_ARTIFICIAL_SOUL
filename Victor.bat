@echo off
if exist "dist\Victor\Victor.exe" (
    start "" "dist\Victor\Victor.exe"
) else (
    call run.bat
)
