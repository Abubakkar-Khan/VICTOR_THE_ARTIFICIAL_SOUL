@echo off
title Dexter — The Artificial Soul Installer
echo ===================================================
echo   Installing Dexter — The Artificial Soul
echo ===================================================
echo.

if not exist "dist\Dexter\Dexter.exe" (
    echo [1/2] Standalone executable not found. Compiling with builder...
    python builder.py --skip-tests
    if %errorlevel% neq 0 (
        echo [ERROR] Build failed during installation.
        pause
        exit /b %errorlevel%
    )
) else (
    echo [1/2] Standalone executable verified: dist\Dexter\Dexter.exe
)

echo.
echo [2/2] Creating Windows Desktop shortcut...
powershell -NoProfile -Command "$ws = New-Object -ComObject WScript.Shell; $d = [Environment]::GetFolderPath('Desktop'); $s = $ws.CreateShortcut(\"$d\Dexter.lnk\"); $p = (Resolve-Path 'dist\Dexter\Dexter.exe').Path; $s.TargetPath = $p; $s.WorkingDirectory = (Resolve-Path 'dist\Dexter').Path; $s.IconLocation = \"$p,0\"; $s.Description = 'Dexter — The Artificial Soul'; $s.Save(); Write-Host 'Desktop shortcut installed successfully!'"

echo.
echo ===================================================
echo   INSTALLATION COMPLETE!
echo   A shortcut with Dexter's pixel icon is on your Desktop:
echo   "Dexter" (C:\Users\HEC\Desktop\Dexter.lnk)
echo.
echo   You can now launch Dexter straight from your Desktop!
echo ===================================================
echo.
set /p launch="Would you like to launch Dexter now? (Y/n): "
if /i "%launch%" neq "n" (
    start "" "dist\Dexter\Dexter.exe"
)
