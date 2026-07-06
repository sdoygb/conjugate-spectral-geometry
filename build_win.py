#!/usr/bin/env python3
"""Windows 全自动安装包构建脚本"""
import shutil, os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
APP_DIR = PROJECT_ROOT / "app"
BUILD_DIR = PROJECT_ROOT / "build_win"

PYTHON_FILES = [
    "server.py", "config.py", "knowledge.py", "models.py",
    "prompts.py", "tools.py", "stream.py", "admin_routes.py",
    "share_routes.py", "auto_teach.py", "start.py", "version.py",
]

def get_version():
    vf = APP_DIR / "version.py"
    for line in vf.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("VERSION"):
            return line.split('"')[1]
    return "unknown"

def copy_source():
    app_target = BUILD_DIR / "app"
    app_target.mkdir(parents=True, exist_ok=True)
    for f in PYTHON_FILES:
        src = APP_DIR / f
        if src.exists():
            shutil.copy2(src, app_target / f)
            print(f"  + {f}")
    for d in ["articles", "templates"]:
        src = APP_DIR / d
        dst = app_target / d
        if src.exists():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            count = sum(1 for _ in dst.rglob("*") if _.is_file())
            print(f"  + {d}/ ({count} files)")
    for f in ["requirements.txt", ".env.example"]:
        src = APP_DIR / f
        if src.exists():
            shutil.copy2(src, app_target / f)

def generate_scripts():
    version = get_version()
    V = version  # shorthand

    # install.bat
    (BUILD_DIR / "install.bat").write_text(
r"""@echo off
chcp 65001 >nul 2>&1
echo.
echo  =========================================================
echo      Geometry AI Server - Windows 安装
echo  =========================================================
echo.

:: 检查管理员权限
net session >nul 2>&1 || (
    echo [!] 请右键"以管理员身份运行"
    pause
    exit /b 1
)

set "APP_DIR=%ProgramFiles%\GeometryAI"
set "SCRIPT_DIR=%~dp0"

set /p DEEPSEEK_KEY="  输入 DeepSeek API Key (必填): "
set /p SILICONFLOW_KEY="  输入 SiliconFlow API Key (可选,直接回车跳过): "
echo.

:: Step 1: Python 3.11+
echo [1/6] 检查 Python 环境...
set "PYTHON="
for %%V in (3.13 3.12 3.11) do (
    where python%%V >nul 2>&1 && (
        set "PYTHON=python%%V"
        goto :found_python
    )
)
where python >nul 2>&1 && (
    for /f "tokens=2 delims= " %%V in ('python --version 2^>^&1') do (
        set "PYTHON=python"
        goto :found_python
    )
)
:found_python
if "%PYTHON%"=="" (
    echo [!] 未找到 Python 3.11+
    echo     请从 https://www.python.org/downloads/ 下载安装
    echo     安装时勾选 "Add Python to PATH"
    pause
    exit /b 1
)
for /f "tokens=2" %%V in ('%PYTHON% --version 2^>^&1') do echo   Python: %PYTHON% %%V

:: Step 2: 安装文件
echo [2/6] 安装程序文件...
if exist "%APP_DIR%" rd /s /q "%APP_DIR%"
xcopy "%SCRIPT_DIR%app" "%APP_DIR%\\" /E /I /Q /Y >nul
mkdir "%APP_DIR%\chroma_db" 2>nul
mkdir "%APP_DIR%\logs" 2>nul
echo   [ok] 文件已安装到 %APP_DIR%

:: 写入 .env
copy "%APP_DIR%\.env.example" "%APP_DIR%\.env" >nul
if not "%DEEPSEEK_KEY%"=="" (
    powershell -Command "(gc '%APP_DIR%\.env') -replace 'GAI_API_KEY=在此', 'GAI_API_KEY=%DEEPSEEK_KEY%' | sc '%APP_DIR%\.env'"
)
if not "%SILICONFLOW_KEY%"=="" (
    powershell -Command "(gc '%APP_DIR%\.env') -replace 'SILICONFLOW_API_KEY=', 'SILICONFLOW_API_KEY=%SILICONFLOW_KEY%' | sc '%APP_DIR%\.env'"
)

:: Step 3: pip 依赖
echo [3/6] 安装 Python 依赖...
%PYTHON% -m pip install --upgrade pip -q 2>nul
%PYTHON% -m pip install -r "%APP_DIR%\requirements.txt" -q 2>nul
echo   [ok] 依赖安装完成

:: Step 4: 注册服务
echo [4/6] 注册 Windows 服务...
sc stop GeometryAI >nul 2>&1
sc delete GeometryAI >nul 2>&1

:: 优先用 NSSM，否则用注册表启动项
where nssm >nul 2>&1
if errorlevel 1 (
    echo   使用注册表启动项方式...
    reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" /v GeometryAI /t REG_SZ /d "%PYTHON% %APP_DIR%\server.py" /f >nul
    echo   [ok] 已添加注册表启动项
    start "" /D "%APP_DIR%" %PYTHON% server.py
) else (
    nssm install GeometryAI "%PYTHON%" "%APP_DIR%\server.py"
    nssm set GeometryAI AppDirectory "%APP_DIR%"
    nssm set GeometryAI DisplayName "Geometry AI Server"
    nssm set GeometryAI Start SERVICE_AUTO_START
    nssm start GeometryAI
    echo   [ok] NSSM 服务已注册
)

echo   等待服务启动...
timeout /t 10 /nobreak >nul

:: Step 5: 安装 Open WebUI
echo [5/7] 安装 Open WebUI...
where open-webui >nul 2>&1
if errorlevel 1 (
    echo   安装 open-webui (可能需要几分钟)...
    %PYTHON% -m pip install open-webui -q 2>nul
)
where open-webui >nul 2>&1
if errorlevel 1 (
    echo   [!] Open WebUI 安装失败，可手动执行: pip install open-webui
) else (
    echo   [ok] Open WebUI 已安装
    :: 注册 Open WebUI 为 NSSM 服务
    where nssm >nul 2>&1
    if not errorlevel 1 (
        nssm install OpenWebUI open-webui serve --port 8080
        nssm set OpenWebUI AppDirectory "%APP_DIR%"
        nssm set OpenWebUI DisplayName "Open WebUI"
        nssm set OpenWebUI Start SERVICE_AUTO_START
        nssm set OpenWebUI AppEnvironmentExtra OPENAI_API_BASE_URLS=http://localhost:5000/v1
        nssm set OpenWebUI AppEnvironmentExtra OPENAI_API_KEYS=%DEEPSEEK_KEY%
        nssm set OpenWebUI AppEnvironmentExtra WEBUI_NAME=Geometry AI
        nssm start OpenWebUI
        echo   [ok] Open WebUI 服务已注册 (端口 8080)
    ) else (
        start "" open-webui serve --port 8080
        echo   [ok] Open WebUI 已启动
    )
)

:: Step 6: 重建索引
echo [6/7] 重建知识库索引...
curl -s -X POST http://localhost:5000/v1/vector/rebuild >nul 2>&1
echo   [ok] 索引重建请求已发送

:: Step 7: 完成
echo.
echo  =========================================================
echo  [ok] 安装完成！
echo  =========================================================
echo.
echo   管理页面: http://localhost:5000/admin
echo   健康检查: http://localhost:5000/health
echo   配置文件: %APP_DIR%\.env
echo.
echo   服务管理: sc start/stop GeometryAI 或 nssm start/stop GeometryAI
echo   卸载: 运行 uninstall.bat
echo.
pause
""", encoding="utf-8")
    print("  + install.bat")

    # fix_index.bat
    (BUILD_DIR / "fix_index.bat").write_text(
r"""@echo off
chcp 65001 >nul 2>&1
echo [1] 检查服务状态...
curl -s http://localhost:5000/health >nul 2>&1
if errorlevel 1 (
    echo [!] 服务未运行，请先启动服务
    pause
    exit /b 1
)
echo   [ok] 服务运行中
echo [2] 触发索引重建...
curl -s -X POST http://localhost:5000/v1/vector/rebuild
echo.
echo   [ok] 索引重建请求已发送
echo   刷新管理页面: http://localhost:5000/admin
pause
""", encoding="utf-8")
    print("  + fix_index.bat")

    # uninstall.bat
    (BUILD_DIR / "uninstall.bat").write_text(
r"""@echo off
chcp 65001 >nul 2>&1
echo.
echo      Geometry AI Server - 卸载
echo.

set "APP_DIR=%ProgramFiles%\GeometryAI"

echo [1/4] 停止服务...
nssm stop GeometryAI >nul 2>&1
nssm remove GeometryAI confirm >nul 2>&1
sc stop GeometryAI >nul 2>&1
sc delete GeometryAI >nul 2>&1
reg delete "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" /v GeometryAI /f >nul 2>&1
echo   [ok] 服务已停止

set /p CONFIRM="是否删除运行时数据？(y/N): "
if /i "%CONFIRM%"=="y" (
    rd /s /q "%APP_DIR%\chroma_db" 2>nul
    rd /s /q "%APP_DIR%\logs" 2>nul
    echo   [ok] 运行时数据已删除
)

set /p CONFIRM2="是否删除整个安装目录？(y/N): "
if /i "%CONFIRM2%"=="y" (
    rd /s /q "%APP_DIR%"
    echo   [ok] 安装目录已删除
)

echo.
echo [ok] 卸载完成
pause
""", encoding="utf-8")
    print("  + uninstall.bat")

def create_zip():
    version = get_version()
    zip_name = f"GeometryAI-Win-Build-v{version}.zip"
    zip_path = PROJECT_ROOT / zip_name
    prefix = f"GeometryAI-Win-Build-v{version}"

    import zipfile
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for script in ["install.bat", "fix_index.bat", "uninstall.bat"]:
            sp = BUILD_DIR / script
            if sp.exists():
                zf.write(sp, f"{prefix}/{script}")
                print(f"  + {script}")
        app_build = BUILD_DIR / "app"
        for file in sorted(app_build.rglob("*")):
            if file.is_file():
                if "__pycache__" in str(file) or file.suffix == ".pyc":
                    continue
                if file.name == ".DS_Store":
                    continue
                rel = file.relative_to(app_build)
                zf.write(file, f"{prefix}/app/{rel}")

    size = zip_path.stat().st_size
    print(f"\n  打包完成: {zip_name} ({size/1024/1024:.1f} MB)")
    print(f"  安装: 解压后右键 install.bat -> 以管理员身份运行")

def build():
    print(f"=== Geometry AI Windows 构建器 v{get_version()} ===\n")
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    BUILD_DIR.mkdir(parents=True)

    print("[1/3] 复制源码...")
    copy_source()

    print("\n[2/3] 生成安装脚本...")
    generate_scripts()

    print("\n[3/3] 打包 zip...")
    create_zip()

    print("\n=== 构建完成 ===")

if __name__ == "__main__":
    build()
