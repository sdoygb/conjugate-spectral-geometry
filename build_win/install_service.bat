@echo off
echo 正在注册 Geometry AI Server 服务...

set "APP_DIR=%~dp0app"
set "PYTHON_DIR=%~dp0python"
set "NSSM=%~dp0nssm.exe"

"%NSSM%" install GeometryAI "%PYTHON_DIR%\python.exe" "%APP_DIR%\server.py"
"%NSSM%" set GeometryAI AppDirectory "%APP_DIR%"
"%NSSM%" set GeometryAI DisplayName "Geometry AI Server"
"%NSSM%" set GeometryAI Description "几何论 AI 学习平台服务"
"%NSSM%" set GeometryAI Start SERVICE_AUTO_START
"%NSSM%" set GeometryAI AppStdout "%~dp0logs\service-stdout.log"
"%NSSM%" set GeometryAI AppStderr "%~dp0logs\service-stderr.log"
"%NSSM%" set GeometryAI AppRotateFiles 1
"%NSSM%" set GeometryAI AppRotateBytes 10485760

echo 服务注册完成，正在启动...
"%NSSM%" start GeometryAI
echo.
echo Geometry AI Server 服务已启动
echo 管理界面: http://localhost:5000/admin
echo.
pause
