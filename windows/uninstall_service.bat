@echo off
echo 正在停止并卸载 Geometry AI Server 服务...
"%~dp0nssm.exe" stop GeometryAI
"%~dp0nssm.exe" remove GeometryAI confirm
echo 服务已卸载
pause
