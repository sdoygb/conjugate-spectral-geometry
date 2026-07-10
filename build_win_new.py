#!/usr/bin/env python3
"""Geometry AI Server - Windows 全自动安装包构建脚本（全新 v2）"""
import shutil, os, stat, zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
APP_DIR = PROJECT_ROOT / "app"
BUILD_DIR = PROJECT_ROOT / "build_win_new"

PYTHON_FILES = [
    "server.py", "config.py", "knowledge.py", "models.py",
    "prompts.py", "tools.py", "stream.py", "admin_routes.py",
    "share_routes.py", "auto_teach.py", "start.py", "version.py",
    "master_client.py",
]
DATA_DIRS = ["articles", "templates"]
IGNORE_DIRS = {"__pycache__", "archive", ".obsidian"}


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

    for d in DATA_DIRS:
        src = APP_DIR / d
        dst = app_target / d
        if src.exists():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst, ignore=lambda d, c: {
                x for x in c if x in IGNORE_DIRS or x == ".DS_Store"
            })
            count = sum(1 for _ in dst.rglob("*") if _.is_file())
            print(f"  + {d}/ ({count} files)")

    for f in ["requirements.txt", ".env.example"]:
        src = APP_DIR / f
        if src.exists():
            shutil.copy2(src, app_target / f)


PS1_SCRIPTS = {
    "install.ps1": """<#
.SYNOPSIS
    Geometry AI Server v{VERSION} - Windows 全自动安装脚本
.DESCRIPTION
    自动安装 Geometry AI Server + Open WebUI + 开机自启
    要求: Windows 10/11, 管理员权限, 需要网络连接
.NOTES
    右键 install.ps1 -> 使用 PowerShell 运行
#>

$ErrorActionPreference = "Stop"
$Host.UI.RawUI.WindowTitle = "Geometry AI Server v{VERSION} - 安装中..."
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$AppDir = Join-Path $env:ProgramFiles "GeometryAI"
$LogFile = Join-Path $env:TEMP "geometry-ai-install.log"

function Write-Log { param([string]$Msg) $Msg | Out-File -FilePath $LogFile -Append; Write-Host $Msg }

Write-Log "========================================================="
Write-Log " Geometry AI Server v{VERSION} - Windows 全自动安装"
Write-Log "========================================================="
Write-Log ""

# ---- Admin Check ----
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "[!] 请以管理员身份运行" -ForegroundColor Red
    Write-Host "    右键 install.ps1 -> 使用 PowerShell 运行" -ForegroundColor Red
    pause; exit 1
}

# ---- Python Detection / Auto-Install ----
function Find-Python {
    foreach ($ver in @("3.13", "3.12", "3.11")) {
        $name = "python$ver"
        $path = (Get-Command $name -ErrorAction SilentlyContinue).Source
        if ($path) { return @{Path=$path; Name=$name} }
    }
    $path = (Get-Command python -ErrorAction SilentlyContinue).Source
    if ($path) {
        try {
            $v = & $path -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
            $major, $minor = $v.Split('.')
            if ([int]$major -eq 3 -and [int]$minor -ge 11) { return @{Path=$path; Name="python"} }
        } catch {}
    }
    return $null
}

function Install-Python {
    Write-Host "  Python 3.11+ not found, installing via winget..." -ForegroundColor Yellow
    try {
        winget install -e --id Python.Python.3.11 --accept-package-agreements --accept-source-agreements 2>&1 | Out-Null
        $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")
        $py = (Get-Command python3.11 -ErrorAction SilentlyContinue).Source
        if (-not $py) { $py = (Get-Command python -ErrorAction SilentlyContinue).Source }
        if ($py) { return @{Path=$py; Name="python"} }
    } catch {
        Write-Host "  winget install failed. Please install Python 3.11+ manually:" -ForegroundColor Red
        Write-Host "  https://www.python.org/downloads/" -ForegroundColor Red
        Write-Host "  Check 'Add Python to PATH' during install" -ForegroundColor Red
        pause; exit 1
    }
}

Write-Host "[1/8] Checking Python..." -ForegroundColor Cyan
$Python = Find-Python
if (-not $Python) { $Python = Install-Python }
$pyVer = & $Python.Path -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"
Write-Host "  Python: $pyVer ($($Python.Path))" -ForegroundColor Green

# ---- Copy Files ----
Write-Host "[2/8] Installing program files..." -ForegroundColor Cyan
if (Test-Path $AppDir) { Remove-Item -Recurse -Force $AppDir -ErrorAction SilentlyContinue }
New-Item -ItemType Directory -Path $AppDir -Force | Out-Null

$SourceApp = Join-Path $ScriptDir "app"
if (-not (Test-Path $SourceApp)) {
    Write-Host "[!] app/ directory not found — install.ps1 must be alongside app/" -ForegroundColor Red
    pause; exit 1
}
Copy-Item -Recurse -Force $SourceApp "$AppDir\\"
New-Item -ItemType Directory -Path (Join-Path $AppDir "chroma_db") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $AppDir "logs") -Force | Out-Null
Write-Host "  Files installed to $AppDir" -ForegroundColor Green

# ---- Virtual Environment ----
Write-Host "[3/8] Creating virtual environment..." -ForegroundColor Cyan
$VenvDir = Join-Path $AppDir ".venv"
& $Python.Path -m venv $VenvDir
$VenvPython = Join-Path $VenvDir "Scripts\\python.exe"
Write-Host "  Venv: $VenvDir" -ForegroundColor Green

# ---- pip Dependencies ----
Write-Host "[4/8] Installing Python dependencies..." -ForegroundColor Cyan
$ReqFile = Join-Path $AppDir "requirements.txt"
$Pip = Join-Path $VenvDir "Scripts\\pip.exe"
& $Pip install --upgrade pip -q

$mirrors = @(
    "https://pypi.tuna.tsinghua.edu.cn/simple",
    "https://mirrors.aliyun.com/pypi/simple/",
    "https://pypi.org/simple"
)
$installed = $false
foreach ($mirror in $mirrors) {
    try {
        & $Pip install -i $mirror -r $ReqFile -q 2>&1 | Out-Null
        $installed = $true
        break
    } catch { continue }
}
if (-not $installed) {
    Write-Host "  [!] Dependency install failed — check network" -ForegroundColor Red
    pause; exit 1
}
Write-Host "  Dependencies installed" -ForegroundColor Green

# ---- .env Configuration ----
Write-Host "[5/8] Configuring API Key..." -ForegroundColor Cyan
$EnvExample = Join-Path $AppDir ".env.example"
$EnvFile = Join-Path $AppDir ".env"

$deepseekKey = ""
while ([string]::IsNullOrWhiteSpace($deepseekKey)) {
    $deepseekKey = Read-Host "  Enter DeepSeek API Key (required, get at https://platform.deepseek.com)"
}
$siliconflowKey = Read-Host "  Enter SiliconFlow API Key (optional, press Enter to skip)"

$envContent = Get-Content $EnvExample -Raw
$envContent = $envContent -replace "GAI_API_KEY=在此", "GAI_API_KEY=$deepseekKey"
if (-not [string]::IsNullOrWhiteSpace($siliconflowKey)) {
    $envContent = $envContent -replace "SILICONFLOW_API_KEY=", "SILICONFLOW_API_KEY=$siliconflowKey"
}
$envContent | Out-File -FilePath $EnvFile -Encoding utf8
Write-Host "  Config saved" -ForegroundColor Green

# ---- Firewall ----
Write-Host "[6/8] Configuring firewall..." -ForegroundColor Cyan
try {
    $rule = Get-NetFirewallRule -DisplayName "Geometry AI Server" -ErrorAction SilentlyContinue
    if (-not $rule) {
        New-NetFirewallRule -DisplayName "Geometry AI Server" -Direction Inbound -Protocol TCP -LocalPort 5000 -Action Allow -ErrorAction SilentlyContinue | Out-Null
        New-NetFirewallRule -DisplayName "Geometry AI Server (8080)" -Direction Inbound -Protocol TCP -LocalPort 8080 -Action Allow -ErrorAction SilentlyContinue | Out-Null
    }
    Write-Host "  Firewall rules added" -ForegroundColor Green
} catch {
    Write-Host "  Firewall config skipped (permission or policy)" -ForegroundColor Yellow
}

# ---- Task Scheduler (Auto-start) ----
Write-Host "[7/8] Registering auto-start (Task Scheduler)..." -ForegroundColor Cyan
$TaskName = "GeometryAI Server"
$TaskUser = "$env:COMPUTERNAME\\$env:USERNAME"

Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
Stop-Process -Name "python" -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

$Action = New-ScheduledTaskAction -Execute $VenvPython -Argument (Join-Path $AppDir "server.py") -WorkingDirectory $AppDir
$Trigger = New-ScheduledTaskTrigger -AtStartup
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
$Principal = New-ScheduledTaskPrincipal -UserId "$env:COMPUTERNAME\\$env:USERNAME" -RunLevel Highest -LogonType Interactive
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Force | Out-Null
Write-Host "  Auto-start registered (Task Scheduler)" -ForegroundColor Green

# ---- Start Service ----
Write-Host "  Starting service..." -ForegroundColor Cyan
try {
    $job = Start-Job -ScriptBlock {
        param($py, $dir)
        Set-Location $dir
        & $py (Join-Path $dir "server.py")
    } -ArgumentList $VenvPython, $AppDir

    Start-Sleep -Seconds 8

    $ok = $false
    for ($i = 0; $i -lt 15; $i++) {
        try {
            $resp = Invoke-WebRequest -Uri "http://localhost:5000/health" -UseBasicParsing -TimeoutSec 3
            if ($resp.StatusCode -eq 200) { $ok = $true; break }
        } catch {}
        Start-Sleep -Seconds 2
    }
    if ($ok) {
        Write-Host "  [OK] Geometry AI Server running (port 5000)" -ForegroundColor Green
    } else {
        Write-Host "  [!] Service start timeout — check logs: $AppDir\\logs" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  [!] Start failed: $_" -ForegroundColor Yellow
}

# ---- Open WebUI ----
Write-Host "  Installing Open WebUI..." -ForegroundColor Cyan
$WebuiVenv = Join-Path $AppDir "open-webui-venv"
try {
    if (Test-Path $WebuiVenv) { Remove-Item -Recurse -Force $WebuiVenv -ErrorAction SilentlyContinue }
    & $VenvPython -m venv $WebuiVenv
    $WebuiPip = Join-Path $WebuiVenv "Scripts\\pip.exe"

    Write-Host "  Installing PyTorch (CPU only, no CUDA)..." -ForegroundColor Gray
    & $WebuiPip install torch --index-url https://download.pytorch.org/whl/cpu -q 2>&1 | Out-Null

    Write-Host "  Installing Open WebUI..." -ForegroundColor Gray
    & $WebuiPip install open-webui -q 2>&1 | Out-Null

    $WebuiBin = Join-Path $WebuiVenv "Scripts\\open-webui.exe"
    if (Test-Path $WebuiBin) {
        $WebuiAction = New-ScheduledTaskAction -Execute $WebuiBin -Argument "serve --port 8080" -WorkingDirectory $AppDir
        $WebuiTaskName = "GeometryAI Open WebUI"
        Unregister-ScheduledTask -TaskName $WebuiTaskName -Confirm:$false -ErrorAction SilentlyContinue
        Register-ScheduledTask -TaskName $WebuiTaskName -Action $WebuiAction -Trigger $Trigger -Settings $Settings -Principal $Principal -Force | Out-Null
        Write-Host "  [OK] Open WebUI installed + auto-start (port 8080)" -ForegroundColor Green

        Start-Job -ScriptBlock {
            param($exe, $dir, $key)
            Set-Location $dir
            $env:OPENAI_API_BASE_URLS = "http://localhost:5000/v1"
            $env:OPENAI_API_KEYS = $key
            $env:WEBUI_NAME = "Geometry AI"
            & $exe serve --port 8080
        } -ArgumentList $WebuiBin, $AppDir, $deepseekKey | Out-Null
    } else {
        Write-Host "  [!] Open WebUI binary not found, skipping" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  [!] Open WebUI install failed: $_" -ForegroundColor Yellow
    Write-Host "  Manual: pip install open-webui" -ForegroundColor Gray
}

# ---- Rebuild Index ----
Write-Host "  Rebuilding knowledge base index..." -ForegroundColor Cyan
Start-Sleep -Seconds 3
try {
    Invoke-WebRequest -Uri "http://localhost:5000/v1/vector/rebuild" -Method POST -UseBasicParsing -TimeoutSec 10 | Out-Null
    Write-Host "  [OK] Index rebuild triggered" -ForegroundColor Green
} catch {
    Write-Host "  [!] Index rebuild failed (run fix-index.ps1 later)" -ForegroundColor Yellow
}

# ---- Desktop Shortcut ----
try {
    $DesktopPath = [Environment]::GetFolderPath("Desktop")
    $ShortcutPath = Join-Path $DesktopPath "Geometry AI Server.url"
    @"
[InternetShortcut]
URL=http://localhost:5000/admin
"@ | Out-File -FilePath $ShortcutPath -Encoding default
    Write-Host "  Desktop shortcut created" -ForegroundColor Green
} catch {}

# ---- Done ----
Write-Log ""
Write-Log "========================================================="
Write-Log "  [OK] Installation complete!"
Write-Log "========================================================="
Write-Log ""
Write-Log "  Admin panel: http://localhost:5000/admin"
Write-Log "  Health:      http://localhost:5000/health"
Write-Log "  Config:      $AppDir\\.env"
Write-Log ""
Write-Log "  Commands (PowerShell Admin):"
Write-Log "    Start:    Start-ScheduledTask -TaskName 'GeometryAI Server'"
Write-Log "    Stop:     Stop-ScheduledTask -TaskName 'GeometryAI Server'"
Write-Log "    Logs:     Get-Content '$AppDir\\logs\\geometry_ai.log' -Tail 50"
Write-Log "    Uninstall: right-click uninstall.ps1 -> Run with PowerShell"
Write-Log ""
Write-Host "  Opening browser..." -ForegroundColor Cyan
Start-Sleep -Seconds 3
try { Start-Process "http://localhost:5000/admin" } catch {}
pause
""",

    "uninstall.ps1": """<#
.SYNOPSIS
    Geometry AI Server v{VERSION} - Uninstall script
#>

$Host.UI.RawUI.WindowTitle = "Geometry AI Server - Uninstall"

if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "[!] Run as Administrator" -ForegroundColor Red
    pause; exit 1
}

Write-Host ""
Write-Host "  Geometry AI Server v{VERSION} - Uninstall" -ForegroundColor Cyan
Write-Host ""

$AppDir = Join-Path $env:ProgramFiles "GeometryAI"

Write-Host "[1/4] Stopping services..." -ForegroundColor Cyan
Stop-Process -Name "python" -Force -ErrorAction SilentlyContinue
Unregister-ScheduledTask -TaskName "GeometryAI Server" -Confirm:$false -ErrorAction SilentlyContinue
Unregister-ScheduledTask -TaskName "GeometryAI Open WebUI" -Confirm:$false -ErrorAction SilentlyContinue
Write-Host "  Services stopped" -ForegroundColor Green

Write-Host "[2/4] Removing firewall rules..." -ForegroundColor Cyan
try {
    Remove-NetFirewallRule -DisplayName "Geometry AI Server" -ErrorAction SilentlyContinue
    Remove-NetFirewallRule -DisplayName "Geometry AI Server (8080)" -ErrorAction SilentlyContinue
    Write-Host "  Firewall rules removed" -ForegroundColor Green
} catch {}

$confirmData = Read-Host "Delete vector database and logs? (y/N)"
if ($confirmData -eq "y" -or $confirmData -eq "Y") {
    if (Test-Path $AppDir) {
        Remove-Item -Recurse -Force (Join-Path $AppDir "chroma_db") -ErrorAction SilentlyContinue
        Remove-Item -Recurse -Force (Join-Path $AppDir "logs") -ErrorAction SilentlyContinue
        Remove-Item -Recurse -Force (Join-Path $AppDir "models_cache") -ErrorAction SilentlyContinue
    }
    Write-Host "  Runtime data deleted" -ForegroundColor Green
}

$confirmDir = Read-Host "Delete entire installation directory? (y/N)"
if ($confirmDir -eq "y" -or $confirmDir -eq "Y") {
    if (Test-Path $AppDir) {
        Remove-Item -Recurse -Force $AppDir -ErrorAction SilentlyContinue
    }
    Write-Host "  Installation directory deleted" -ForegroundColor Green
}

try {
    $DesktopPath = [Environment]::GetFolderPath("Desktop")
    $ShortcutPath = Join-Path $DesktopPath "Geometry AI Server.url"
    if (Test-Path $ShortcutPath) { Remove-Item -Force $ShortcutPath }
}

Write-Host ""
Write-Host "[OK] Uninstall complete" -ForegroundColor Green
pause
""",

    "fix-index.ps1": """<#
.SYNOPSIS
    Rebuild Geometry AI Server knowledge base index
#>

$Host.UI.RawUI.WindowTitle = "Geometry AI Server - Rebuild Index"

try {
    $resp = Invoke-WebRequest -Uri "http://localhost:5000/health" -UseBasicParsing -TimeoutSec 5
    if ($resp.StatusCode -ne 200) { throw "Service not ready" }
    Write-Host "[OK] Service is running" -ForegroundColor Green
} catch {
    Write-Host "[!] Geometry AI Server is not running" -ForegroundColor Red
    Write-Host "    Start it from Task Scheduler: GeometryAI Server" -ForegroundColor Yellow
    pause; exit 1
}

Write-Host "Rebuilding knowledge base index..." -ForegroundColor Cyan
try {
    $resp = Invoke-WebRequest -Uri "http://localhost:5000/v1/vector/rebuild" -Method POST -UseBasicParsing -TimeoutSec 120
    Write-Host "[OK] Index rebuilt" -ForegroundColor Green
    Write-Host "Refresh admin panel: http://localhost:5000/admin" -ForegroundColor Cyan
} catch {
    Write-Host "[!] Index rebuild failed: $_" -ForegroundColor Red
    Write-Host "    Check service logs" -ForegroundColor Yellow
}
pause
""",
}

# Batch launchers — .bat is natively double-clickable on Windows
# They auto-elevate to admin and call the corresponding .ps1
BAT_LAUNCHER = """@echo off
chcp 65001 >nul 2>&1
set "PS1=%~dp0{NAME}.ps1"
if not exist "%PS1%" (
    echo [!] {NAME}.ps1 not found — make sure it's in the same folder
    pause
    exit /b 1
)
:: Auto-elevate to admin if not already
net session >nul 2>&1
if errorlevel 1 (
    echo Requesting administrator privileges...
    powershell -NoProfile -Command "Start-Process powershell '-NoProfile -ExecutionPolicy Bypass -File \"%~dp0{NAME}.ps1\"' -Verb RunAs"
    exit /b 0
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%PS1%"
pause
"""


def _write_bat(name: str):
    """Write a .bat launcher for a .ps1 script"""
    text = BAT_LAUNCHER.replace("{NAME}", name)
    path = BUILD_DIR / f"{name}.bat"
    path.write_text(text, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IRWXU | stat.S_IRWXG)
    print(f"  + {name}.bat (双击运行)")


def generate_scripts():
    version = get_version()

    for name, content in PS1_SCRIPTS.items():
        text = content.replace("{VERSION}", version)
        path = BUILD_DIR / name
        path.write_text(text, encoding="utf-8")
        path.chmod(path.stat().st_mode | stat.S_IRWXU | stat.S_IRWXG)
        print(f"  + {name}")

    for short in ["install", "uninstall", "fix-index"]:
        _write_bat(short)


def build():
    global version
    version = get_version()
    print(f"=== Geometry AI Windows 安装包构建 v{version} ===\n")

    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    BUILD_DIR.mkdir(parents=True)

    print("[1/3] 复制源码...")
    copy_source()

    print("\n[2/3] 生成安装脚本...")
    generate_scripts()

    print("\n[3/3] 打包 zip...")
    zip_name = f"GeometryAI-Win-Build-v{version}.zip"
    zip_path = PROJECT_ROOT / zip_name
    prefix = f"GeometryAI-Win-Build-v{version}"

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for script in ["install.ps1", "uninstall.ps1", "fix-index.ps1",
                        "install.bat", "uninstall.bat", "fix-index.bat"]:
            sp = BUILD_DIR / script
            if sp.exists():
                zf.write(sp, f"{prefix}/{script}")

        app_build = BUILD_DIR / "app"
        for file in sorted(app_build.rglob("*")):
            if file.is_file():
                if "__pycache__" in str(file) or file.suffix == ".pyc":
                    continue
                if file.name == ".DS_Store":
                    continue
                rel = file.relative_to(app_build)
                zf.write(file, f"{prefix}/app/{rel}")

    size = zip_path.stat().st_size / (1024 * 1024)
    print(f"\n  打包完成: {zip_name} ({size:.1f} MB)")
    print(f"  安装: 解压后双击 install.bat（自动提权）")


if __name__ == "__main__":
    build()
