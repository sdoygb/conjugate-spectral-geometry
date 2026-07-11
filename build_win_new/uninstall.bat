@echo off
chcp 65001 >nul 2>&1
set "PS1=%~dp0uninstall.ps1"
if not exist "%PS1%" (
    echo [!] uninstall.ps1 not found — make sure it's in the same folder
    pause
    exit /b 1
)
:: Auto-elevate to admin if not already
net session >nul 2>&1
if errorlevel 1 (
    echo Requesting administrator privileges...
    powershell -NoProfile -Command "Start-Process powershell '-NoProfile -ExecutionPolicy Bypass -File "%~dp0uninstall.ps1"' -Verb RunAs"
    exit /b 0
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%PS1%"
pause
