@echo off
title Victor — The Artificial Soul Installer
echo ===================================================
echo   Installing Victor — The Artificial Soul
echo ===================================================
echo.

if not exist "dist\Victor\Victor.exe" (
    echo [1/2] Standalone executable not found. Compiling with builder...
    python builder.py --skip-tests
    if %errorlevel% neq 0 (
        echo [ERROR] Build failed during installation.
        pause
        exit /b %errorlevel%
    )
) else (
    echo [1/2] Standalone executable verified: dist\Victor\Victor.exe
)

echo.
echo [2/2] Creating Windows Desktop shortcut...
powershell -NoProfile -Command "$ws = New-Object -ComObject WScript.Shell; $d = [Environment]::GetFolderPath('Desktop'); $s = $ws.CreateShortcut(\"$d\Victor.lnk\"); $p = (Resolve-Path 'dist\Victor\Victor.exe').Path; $s.TargetPath = $p; $s.WorkingDirectory = (Resolve-Path 'dist\Victor').Path; $s.IconLocation = \"$p,0\"; $s.Description = 'Victor — The Artificial Soul'; $s.Save(); Write-Host 'Desktop shortcut installed successfully!'"

echo.
echo ===================================================
echo   INSTALLATION COMPLETE!
echo   A shortcut with Victor's pixel icon is on your Desktop:
echo   "Victor" (C:\Users\HEC\Desktop\Victor.lnk)
echo.
echo   You can now launch Victor straight from your Desktop!
echo ===================================================
echo.
set /p launch="Would you like to launch Victor now? (Y/n): "
if /i "%launch%" neq "n" (
    start "" "dist\Victor\Victor.exe"
)
