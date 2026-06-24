@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
title Geometry AI Server - 全自动安装

echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║     Geometry AI Server - 全自动安装程序          ║
echo  ║     双击此文件，等待安装完成即可                  ║
echo  ╚══════════════════════════════════════════════════╝
echo.

:: ============================================================
:: 配置
:: ============================================================
set "INSTALL_DIR=%~dp0"
set "INSTALL_DIR=%INSTALL_DIR:~0,-1%"
set "PYTHON_VERSION=3.11.9"
set "PYTHON_URL=https://www.python.org/ftp/python/%PYTHON_VERSION%/python-%PYTHON_VERSION%-embed-amd64.zip"
set "NSSM_URL=https://nssm.cc/release/nssm-2.24.zip"
set "PIP_URL=https://bootstrap.pypa.io/get-pip.py"

:: ============================================================
:: Step 1: 检查是否已安装
:: ============================================================
if exist "%INSTALL_DIR%\python\python.exe" (
    if exist "%INSTALL_DIR%\python\Lib\site-packages\flask" (
        echo [√] Python 和依赖已安装，跳过下载
        goto :config
    )
)

:: ============================================================
:: Step 2: 下载 Python 嵌入式版本
:: ============================================================
echo.
echo [1/5] 下载 Python %PYTHON_VERSION% ...
if not exist "%INSTALL_DIR%\python\python.exe" (
    mkdir "%INSTALL_DIR%\python" 2>nul
    echo 正在下载，请稍候（约15MB）...
    powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%INSTALL_DIR%\python\python.zip'" 2>nul
    if errorlevel 1 (
        echo [!] 下载失败，请检查网络连接
        echo     也可以手动下载: %PYTHON_URL%
        echo     解压到: %INSTALL_DIR%\python\
        pause
        exit /b 1
    )
    echo 正在解压...
    powershell -Command "Expand-Archive -Path '%INSTALL_DIR%\python\python.zip' -DestinationPath '%INSTALL_DIR%\python\' -Force"
    del "%INSTALL_DIR%\python\python.zip" 2>nul
    echo [√] Python 解压完成
) else (
    echo [√] Python 已存在
)

:: ============================================================
:: Step 3: 配置 Python 并安装 pip
:: ============================================================
echo.
echo [2/5] 配置 Python 环境...

:: 修改 python311._pth 启用 site-packages
set "PTH_FILE=%INSTALL_DIR%\python\python311._pth"
if exist "%PTH_FILE%" (
    echo python311.zip> "%PTH_FILE%"
    echo .>> "%PTH_FILE%"
    echo Lib\>> "%PTH_FILE%"
    echo Lib\site-packages>> "%PTH_FILE%"
    echo import site>> "%PTH_FILE%"
    echo [√] Python 路径配置完成
)

:: 安装 pip
if not exist "%INSTALL_DIR%\python\Lib\site-packages\pip" (
    echo 正在安装 pip...
    powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%PIP_URL%' -OutFile '%INSTALL_DIR%\python\get-pip.py'" 2>nul
    "%INSTALL_DIR%\python\python.exe" "%INSTALL_DIR%\python\get-pip.py" --no-warn-script-location 2>nul
    del "%INSTALL_DIR%\python\get-pip.py" 2>nul
    echo [√] pip 安装完成
) else (
    echo [√] pip 已存在
)

:: ============================================================
:: Step 4: 安装 Python 依赖
:: ============================================================
echo.
echo [3/5] 安装 Python 依赖（可能需要几分钟）...
"%INSTALL_DIR%\python\python.exe" -m pip install --target="%INSTALL_DIR%\python\Lib\site-packages" -r "%INSTALL_DIR%\app\requirements.txt" --quiet --disable-pip-version-check 2>nul
if errorlevel 1 (
    echo [!] 依赖安装失败，尝试逐个安装...
    for %%p in (openai flask flask_cors chromadb fastembed) do (
        echo   安装 %%p ...
        "%INSTALL_DIR%\python\python.exe" -m pip install --target="%INSTALL_DIR%\python\Lib\site-packages" %%p --quiet --disable-pip-version-check 2>nul
    )
)
echo [√] Python 依赖安装完成

:: ============================================================
:: Step 5: 下载 NSSM
:: ============================================================
echo.
echo [4/5] 下载 NSSM（Windows 服务管理器）...
if not exist "%INSTALL_DIR%\nssm.exe" (
    echo 正在下载...
    powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%NSSM_URL%' -OutFile '%INSTALL_DIR%\nssm.zip'" 2>nul
    if errorlevel 1 (
        echo [!] NSSM 下载失败，将使用手动启动模式
        goto :config
    )
    powershell -Command "Expand-Archive -Path '%INSTALL_DIR%\nssm.zip' -DestinationPath '%INSTALL_DIR%\nssm_temp' -Force"
    copy "%INSTALL_DIR%\nssm_temp\nssm-2.24\win64\nssm.exe" "%INSTALL_DIR%\nssm.exe" 2>nul
    if not exist "%INSTALL_DIR%\nssm.exe" (
        copy "%INSTALL_DIR%\nssm_temp\nssm-2.24\win32\nssm.exe" "%INSTALL_DIR%\nssm.exe" 2>nul
    )
    rmdir /s /q "%INSTALL_DIR%\nssm_temp" 2>nul
    del "%INSTALL_DIR%\nssm.zip" 2>nul
    if exist "%INSTALL_DIR%\nssm.exe" (
        echo [√] NSSM 下载完成
    ) else (
        echo [!] NSSM 解压失败，将使用手动启动模式
    )
) else (
    echo [√] NSSM 已存在
)

:: ============================================================
:: Step 6: 配置
:: ============================================================
:config
echo.
echo [5/5] 配置 API Key...
echo.

:: 检查是否已有配置
set "ENV_FILE=%INSTALL_DIR%\app\.env"
if exist "%ENV_FILE%" (
    echo 检测到已有配置文件
    findstr /C:"GAI_API_KEY=" "%ENV_FILE%" >nul 2>&1
    if not errorlevel 1 (
        echo 配置已存在，跳过（如需修改请编辑 %ENV_FILE%）
        goto :start
    )
)

:: 输入 API Key
echo 免费注册: https://platform.deepseek.com/
set /p "API_KEY=请输入你的 DeepSeek API Key（在 https://platform.deepseek.com 获取）: "
if "%API_KEY%"=="" (
    echo [!] API Key 不能为空
    pause
    exit /b 1
)

echo.
echo  请输入你的 SiliconFlow API Key（向量数据库，免费注册: https://cloud.siliconflow.cn/）
echo  （如果跳过，将使用本地 embedding 模型）
set /p "SILICONFLOW_KEY=  SiliconFlow API Key: "
if "%SILICONFLOW_KEY%"=="" set SILICONFLOW_KEY=not-needed

:: 写入配置
(
    echo # Geometry AI Server 配置
    echo GAI_API_KEY=%API_KEY%
    echo GAI_BASE_URL=https://api.deepseek.com/v1
    echo GAI_MODEL=deepseek-v4-pro
    echo GAI_MODEL_LITE=deepseek-v4-flash
    echo GAI_MODEL_VISION=deepseek-v4-flash
    echo GAI_EMBEDDING_MODEL=deepseek-v4-flash
    echo GAI_EMBEDDING_MODE=siliconflow
    echo SILICONFLOW_API_KEY=%SILICONFLOW_KEY%
) > "%ENV_FILE%"
echo [√] 配置已保存

:: ============================================================
:: Step 7: 创建日志目录
:: ============================================================
if not exist "%INSTALL_DIR%\logs" mkdir "%INSTALL_DIR%\logs"

:: ============================================================
:: Step 8: 启动服务
:: ============================================================
:start
echo.
echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║     安装完成！正在启动服务...                    ║
echo  ╚══════════════════════════════════════════════════╝
echo.

:: 注册 Windows 服务（如果 NSSM 可用）
if exist "%INSTALL_DIR%\nssm.exe" (
    echo 正在注册 Windows 服务...
    "%INSTALL_DIR%\nssm.exe" stop GeometryAI 2>nul
    "%INSTALL_DIR%\nssm.exe" remove GeometryAI 2>nul
    "%INSTALL_DIR%\nssm.exe" install GeometryAI "%INSTALL_DIR%\python\python.exe" "%INSTALL_DIR%\app\server.py"
    "%INSTALL_DIR%\nssm.exe" set GeometryAI AppDirectory "%INSTALL_DIR%\app"
    "%INSTALL_DIR%\nssm.exe" set GeometryAI DisplayName "Geometry AI Server"
    "%INSTALL_DIR%\nssm.exe" set GeometryAI Description "几何论 AI 学习平台服务"
    "%INSTALL_DIR%\nssm.exe" set GeometryAI Start SERVICE_AUTO_START
    "%INSTALL_DIR%\nssm.exe" set GeometryAI AppStdout "%INSTALL_DIR%\logs\service-stdout.log"
    "%INSTALL_DIR%\nssm.exe" set GeometryAI AppStderr "%INSTALL_DIR%\logs\service-stderr.log"
    "%INSTALL_DIR%\nssm.exe" set GeometryAI AppRotateFiles 1
    "%INSTALL_DIR%\nssm.exe" set GeometryAI AppRotateBytes 10485760
    "%INSTALL_DIR%\nssm.exe" start GeometryAI
    echo [√] Windows 服务已注册并启动（开机自动运行）
    echo.
    echo     管理界面: http://localhost:5000/admin
    echo     聊天界面: http://localhost:3000 （需单独安装 Open WebUI）
    echo.
    echo     停止服务: 运行 uninstall_service.bat
    echo     手动启动: 运行 start.bat
) else (
    echo NSSM 不可用，使用手动启动模式...
    echo.
    echo 正在启动服务（此窗口不要关闭）...
    echo.
    echo     管理界面: http://localhost:5000/admin
    echo.
    start http://localhost:5000/admin
    cd /d "%INSTALL_DIR%\app"
    "%INSTALL_DIR%\python\python.exe" server.py
    pause
    exit /b 0
)

:: 等待服务启动后打开浏览器
echo 正在等待服务启动...
set /a "WAIT=0"
:wait_loop
if %WAIT% geq 30 (
    echo [!] 服务启动超时，请手动打开 http://localhost:5000/admin
    goto :done
)
timeout /t 2 /nobreak >nul
set /a "WAIT+=2"
powershell -Command "try { (Invoke-WebRequest -Uri 'http://localhost:5000/health' -TimeoutSec 2 -UseBasicParsing).StatusCode } catch { exit 1 }" 2>nul
if errorlevel 1 goto :wait_loop

echo [√] 服务已启动！
start http://localhost:5000/admin

:done
echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║     安装完成！                                   ║
echo  ║                                                  ║
echo  ║     管理界面: http://localhost:5000/admin        ║
echo  ║     聊天界面: http://localhost:3000               ║
echo  ║                                                  ║
echo  ║     停止服务: 双击 uninstall_service.bat         ║
echo  ║     手动启动: 双击 start.bat                     ║
echo  ║     修改配置: 编辑 app\.env 文件                 ║
echo  ╚══════════════════════════════════════════════════╝
echo.
pause
