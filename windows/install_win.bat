@echo off
chcp 65001 >nul 2>&1
title Geometry AI Server - Windows 全自动安装
setlocal enabledelayedexpansion

echo.
echo  ========================================================
echo      Geometry AI Server - Windows 全自动安装
echo      双击此文件，等待安装完成即可
echo  ========================================================
echo.

REM 安装目录（脚本所在目录）
set "INSTALL_DIR=%~dp0"
set "INSTALL_DIR=%INSTALL_DIR:~0,-1%"
set "APP_DIR=%INSTALL_DIR%\app"
set "LOG_DIR=%INSTALL_DIR%\logs"

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

REM ============================================================
REM Step 1: 准备 Python 环境
REM ============================================================
echo [1/6] 准备 Python 环境...

REM 清除可能干扰的环境变量
set "PYTHONHOME="
set "PYTHONPATH="

REM 查找 Python 3.11+
set "PYTHON="
for %%P in (
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    "C:\Python311\python.exe"
    "C:\Python312\python.exe"
    "C:\Python313\python.exe"
) do (
    if exist %%P (
        set "PYTHON=%%~P"
        goto :found_python
    )
)

REM 尝试系统 PATH 中的 python
where python >nul 2>&1
if %errorlevel%==0 (
    for /f "delims=" %%P in ('python --version 2^>^&1') do (
        echo %%P | findstr "3.1[1-9]" >nul && (
            set "PYTHON=python"
            goto :found_python
        )
    )
)

REM 尝试使用安装包自带的 Python
if exist "%INSTALL_DIR%\python3.11.exe" (
    echo   正在安装 Python 3.11...
    "%INSTALL_DIR%\python3.11.exe" /quiet InstallAllUsers=0 PrependPath=1
    timeout /t 10 /nobreak >nul
    set "PYTHON=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
)

:found_python
if not defined PYTHON (
    echo [!] 未找到合适的 Python（需要 3.11+）
    echo   请先安装 Python 3.11: https://www.python.org/downloads/
    echo   安装时请勾选 "Add Python to PATH"
    pause
    exit /b 1
)

for /f "delims=" %%V in ('"%PYTHON%" --version 2^>^&1') do set "PY_VERSION=%%V"
echo [√] %PY_VERSION%: %PYTHON%

REM ============================================================
REM Step 2: 安装 Geometry AI Server 依赖
REM ============================================================
echo.
echo [2/6] 安装 Geometry AI Server 依赖...

"%PYTHON%" -c "import flask" >nul 2>&1
if %errorlevel%==0 (
    echo [√] 依赖已安装，跳过
) else (
    echo   正在安装依赖（可能需要几分钟）...
    "%PYTHON%" -m pip install --quiet --disable-pip-version-check -r "%APP_DIR%\requirements.txt"
    if %errorlevel% neq 0 (
        echo [!] 批量安装失败，逐个安装...
        for %%P in (openai flask flask-cors chromadb python-dotenv) do (
            "%PYTHON%" -m pip install --quiet --disable-pip-version-check %%P
        )
    )
    echo [√] 依赖安装完成
)

REM ============================================================
REM Step 3: 配置 API Key
REM ============================================================
echo.
echo [3/6] 配置 API Key...

set "ENV_FILE=%APP_DIR%\.env"
set "NEED_CONFIG=0"

if exist "%ENV_FILE%" (
    findstr /C:"GAI_API_KEY=" "%ENV_FILE%" >nul 2>&1
    if %errorlevel%==0 (
        findstr /C:"GAI_API_KEY=在此" "%ENV_FILE%" >nul 2>&1
        if %errorlevel%==0 set "NEED_CONFIG=1"
    ) else (
        set "NEED_CONFIG=1"
    )
) else (
    set "NEED_CONFIG=1"
)

if "%NEED_CONFIG%"=="1" (
    echo.
    echo   免费注册: https://platform.deepseek.com/
    echo   请输入你的 DeepSeek API Key
    echo   获取地址: https://platform.deepseek.com
    echo.
    set /p "API_KEY=  API Key: "

    if "!API_KEY!"=="" (
        echo [!] API Key 不能为空
        pause
        exit /b 1
    )

    echo.
    echo   请输入你的 SiliconFlow API Key（向量数据库，免费注册: https://cloud.siliconflow.cn/）
    echo   （如果跳过，将使用本地 embedding 模型）
    set /p "SILICONFLOW_KEY=  SiliconFlow API Key: "
    if "!SILICONFLOW_KEY!"=="" set SILICONFLOW_KEY=not-needed

    (
        echo # Geometry AI Server 配置
        echo GAI_API_KEY=!API_KEY!
        echo GAI_BASE_URL=https://api.deepseek.com/v1
        echo GAI_MODEL=deepseek-v4-pro
        echo GAI_MODEL_LITE=deepseek-v4-flash
        echo GAI_MODEL_VISION=deepseek-v4-flash
        echo GAI_EMBEDDING_MODEL=deepseek-v4-flash
        echo GAI_EMBEDDING_MODE=siliconflow
        echo SILICONFLOW_API_KEY=!SILICONFLOW_KEY!
    ) > "%ENV_FILE%"
    echo [√] 配置已保存
) else (
    echo [√] 配置已存在，跳过
)

REM ============================================================
REM Step 4: 启动 Geometry AI Server
REM ============================================================
echo.
echo [4/6] 启动 Geometry AI Server...

REM 停止旧服务
sc stop GeometryAIServer >nul 2>&1
for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":5000" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%P >nul 2>&1
)
timeout /t 2 /nobreak >nul

REM 创建 Windows 服务（使用 nssm 或直接注册启动项）
REM 先尝试用 nssm
where nssm >nul 2>&1
if %errorlevel%==0 (
    nssm stop GeometryAIServer >nul 2>&1
    nssm remove GeometryAIServer confirm >nul 2>&1
    nssm install GeometryAIServer "%PYTHON%" "%APP_DIR%\server.py"
    nssm set GeometryAIServer AppDirectory "%APP_DIR%"
    nssm set GeometryAIServer AppEnvironmentExtra GEOMETRY_AI_HOME "%INSTALL_DIR%"
    nssm set GeometryAIServer AppEnvironmentExtra PYTHONHOME ""
    nssm set GeometryAIServer AppEnvironmentExtra PYTHONPATH ""
    nssm set GeometryAIServer DisplayName "Geometry AI Server"
    nssm set GeometryAIServer Description "Geometry AI 中间层服务"
    nssm set GeometryAIServer Start SERVICE_AUTO_START
    nssm set GeometryAIServer ObjectName LocalSystem
    nssm set GeometryAIServer AppStdout "%LOG_DIR%\server-stdout.log"
    nssm set GeometryAIServer AppStderr "%LOG_DIR%\server-stderr.log"
    nssm start GeometryAIServer
    echo [√] 已注册为 Windows 服务（开机自启）
) else (
    REM 没有 nssm，用启动项注册
    echo   未安装 nssm，使用启动项方式（开机自启）

    REM 创建启动脚本
    echo @echo off > "%APP_DIR%\start_server.bat"
    echo set "PYTHONHOME=" >> "%APP_DIR%\start_server.bat"
    echo set "PYTHONPATH=" >> "%APP_DIR%\start_server.bat"
    echo set "GEOMETRY_AI_HOME=%INSTALL_DIR%" >> "%APP_DIR%\start_server.bat"
    echo start /b "" "%PYTHON%" "%APP_DIR%\server.py" >> "%APP_DIR%\start_server.bat"

    REM 注册开机启动项（当前用户）
    reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "GeometryAIServer" /t REG_SZ /d "\"%APP_DIR%\start_server.bat\"" /f >nul 2>&1

    REM 立即启动
    start /b "" "%PYTHON%" "%APP_DIR%\server.py" >nul 2>&1
    echo [√] 已注册为开机启动项
)

REM 等待启动
echo   等待服务启动...
set "WAITED=0"
:wait_server
if %WAITED% geq 30 goto :server_timeout
timeout /t 2 /nobreak >nul
curl -s http://localhost:5000/health >nul 2>&1
if %errorlevel%==0 (
    echo [√] Geometry AI Server 已启动（端口 5000）
    goto :server_ok
)
set /a WAITED+=2
goto :wait_server
:server_timeout
echo [!] Geometry AI Server 启动较慢，请稍候...
:server_ok

REM ============================================================
REM Step 5: 安装并启动 Open WebUI
REM ============================================================
echo.
echo [5/6] 安装 Open WebUI（聊天界面）...

REM 设置 HuggingFace 镜像（国内网络加速）
set "HF_ENDPOINT=https://hf-mirror.com"
set "SENTENCE_TRANSFORMERS_HOME=%INSTALL_DIR%\models_cache"

"%PYTHON%" -c "import open_webui" >nul 2>&1
if %errorlevel%==0 (
    echo [√] Open WebUI 已安装
) else (
    echo   正在安装 Open WebUI（需要几分钟，首次会下载模型）...
    echo   使用国内镜像加速...
    "%PYTHON%" -m pip install --quiet --disable-pip-version-check -i https://pypi.tuna.tsinghua.edu.cn/simple open-webui
    if %errorlevel%==0 (
        echo [√] Open WebUI 安装完成
    ) else (
        echo [!] Open WebUI 安装失败，聊天功能暂不可用
        echo   可稍后手动运行: %PYTHON% -m pip install open-webui
        set "WEBUI_SKIP=1"
    )
)

if not defined WEBUI_SKIP (
    REM 查找 open-webui 命令
    set "WEBUI_BIN="
    for %%B in (
        "%LOCALAPPDATA%\Programs\Python\Python311\Scripts\open-webui.exe"
        "%LOCALAPPDATA%\Programs\Python\Python312\Scripts\open-webui.exe"
        "%LOCALAPPDATA%\Programs\Python\Python313\Scripts\open-webui.exe"
    ) do (
        if exist %%B (
            set "WEBUI_BIN=%%~B"
            goto :found_webui
        )
    )

    REM 尝试 PATH
    where open-webui >nul 2>&1
    if %errorlevel%==0 (
        set "WEBUI_BIN=open-webui"
        goto :found_webui
    )

    REM 用 python -m
    set "WEBUI_BIN=%PYTHON%"
    set "WEBUI_ARGS=-m open_webui.main"

    :found_webui
    echo.
    echo   正在启动 Open WebUI（首次启动需下载模型，请耐心等待）...

    REM 停止旧进程
    for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":8080" ^| findstr "LISTENING"') do (
        taskkill /F /PID %%P >nul 2>&1
    )
    timeout /t 2 /nobreak >nul

    REM 创建启动脚本
    echo @echo off > "%APP_DIR%\start_webui.bat"
    echo set "PYTHONHOME=" >> "%APP_DIR%\start_webui.bat"
    echo set "PYTHONPATH=" >> "%APP_DIR%\start_webui.bat"
    echo set "OPENAI_API_BASE_URLS=http://localhost:5000/v1" >> "%APP_DIR%\start_webui.bat"
    echo set "OPENAI_API_KEYS=not-needed" >> "%APP_DIR%\start_webui.bat"
    echo set "HF_ENDPOINT=https://hf-mirror.com" >> "%APP_DIR%\start_webui.bat"
    echo set "SENTENCE_TRANSFORMERS_HOME=%INSTALL_DIR%\models_cache" >> "%APP_DIR%\start_webui.bat"
    if defined WEBUI_ARGS (
        echo start /b "" "%PYTHON%" -m open_webui.main >> "%APP_DIR%\start_webui.bat"
    ) else (
        echo start /b "" "%WEBUI_BIN%" serve >> "%APP_DIR%\start_webui.bat"
    )

    REM 注册开机启动项
    reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "GeometryAIWebUI" /t REG_SZ /d "\"%APP_DIR%\start_webui.bat\"" /f >nul 2>&1

    REM 立即启动
    if defined WEBUI_ARGS (
        start /b "" "%PYTHON%" -m open_webui.main >nul 2>&1
    ) else (
        start /b "" "%WEBUI_BIN%" serve >nul 2>&1
    )

    echo   首次启动需要下载嵌入模型（约 90MB），请耐心等待...
    echo   如果网络较慢，可能需要 5-10 分钟

    REM 等待启动（最多5分钟）
    set "WAITED=0"
    :wait_webui
    if %WAITED% geq 300 goto :webui_timeout
    timeout /t 2 /nobreak >nul
    curl -s http://localhost:8080 >nul 2>&1
    if %errorlevel%==0 (
        echo [√] Open WebUI 已启动（端口 8080）
        goto :webui_ok
    )
    set /a WAITED+=2
    goto :wait_webui
    :webui_timeout
    echo [!] Open WebUI 启动超时
    echo   请稍后访问 http://localhost:8080
    echo   查看日志: %LOG_DIR%\webui-stderr.log
    :webui_ok
)

REM ============================================================
REM Step 6: 打开浏览器
REM ============================================================
echo.
echo [6/6] 打开浏览器...

timeout /t 1 /nobreak >nul

start http://localhost:5000/admin
curl -s http://localhost:8080 >nul 2>&1
if %errorlevel%==0 start http://localhost:8080

echo.
echo  ========================================================
echo      安装完成！
echo
echo      管理界面: http://localhost:5000/admin
echo      聊天界面: http://localhost:8080
echo
echo      聊天界面首次使用：
echo      1. 打开 http://localhost:8080
echo      2. 注册管理员账号
echo      3. 登录后点左下角头像 - Settings
echo      4. 左侧选 Connections
echo      5. 确认 URL 为 http://localhost:5000/v1
echo      6. 回到聊天页，选择 deepseek-v4-pro 模型
echo      7. 开始聊天！
echo
echo      两个服务已设置为开机自动启动
echo
echo      卸载: 双击 uninstall_win.bat
echo  ========================================================
echo.

pause
exit /b 0
