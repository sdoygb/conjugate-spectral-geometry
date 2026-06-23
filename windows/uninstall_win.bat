@echo off
title Geometry AI Server - 卸载
setlocal enabledelayedexpansion

echo.
echo  ========================================================
echo      Geometry AI Server - 卸载
echo  ========================================================
echo.

set "INSTALL_DIR=%~dp0"
set "INSTALL_DIR=%INSTALL_DIR:~0,-1%"
set "APP_DIR=%INSTALL_DIR%\app"

echo   正在停止服务...

REM 停止 Windows 服务（如果用 nssm 注册的）
where nssm >nul 2>&1
if %errorlevel%==0 (
    nssm stop GeometryAIServer >nul 2>&1
    nssm remove GeometryAIServer confirm >nul 2>&1
)

REM 删除开机启动项
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "GeometryAIServer" /f >nul 2>&1
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "GeometryAIWebUI" /f >nul 2>&1

REM 杀掉残留进程
for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":5000" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%P >nul 2>&1
)
for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":8080" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%P >nul 2>&1
)

REM 删除启动脚本
del /f "%APP_DIR%\start_server.bat" >nul 2>&1
del /f "%APP_DIR%\start_webui.bat" >nul 2>&1

echo [√] 服务已停止，开机启动项已删除
echo.
echo   数据文件（.env、知识库等）保留在安装目录中。
echo   如需彻底删除，请手动删除整个安装目录。
echo.
pause
