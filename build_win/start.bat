@echo off
cd /d "%~dp0app"
echo 正在启动 Geometry AI Server...
echo 管理界面: http://localhost:5000/admin
echo 按 Ctrl+C 停止
echo.
"%~dp0python\python.exe" server.py
pause
