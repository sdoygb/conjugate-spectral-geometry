<#
.SYNOPSIS
    Geometry AI Server v1.0.0.0707 - Windows 全自动安装脚本
.DESCRIPTION
    自动安装 Geometry AI Server + Open WebUI + 开机自启
    要求: Windows 10/11, 管理员权限, 需要网络连接
.NOTES
    右键 install.ps1 -> 使用 PowerShell 运行
#>

$ErrorActionPreference = "Stop"
$Host.UI.RawUI.WindowTitle = "Geometry AI Server v1.0.0.0707 - 安装中..."
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$AppDir = Join-Path $env:ProgramFiles "GeometryAI"
$LogFile = Join-Path $env:TEMP "geometry-ai-install.log"

function Write-Log { param([string]$Msg) $Msg | Out-File -FilePath $LogFile -Append; Write-Host $Msg }

Write-Log "========================================================="
Write-Log " Geometry AI Server v1.0.0.0707 - Windows 全自动安装"
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
Copy-Item -Recurse -Force $SourceApp "$AppDir\"
New-Item -ItemType Directory -Path (Join-Path $AppDir "chroma_db") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $AppDir "logs") -Force | Out-Null
Write-Host "  Files installed to $AppDir" -ForegroundColor Green

# ---- Virtual Environment ----
Write-Host "[3/8] Creating virtual environment..." -ForegroundColor Cyan
$VenvDir = Join-Path $AppDir ".venv"
& $Python.Path -m venv $VenvDir
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
Write-Host "  Venv: $VenvDir" -ForegroundColor Green

# ---- pip Dependencies ----
Write-Host "[4/8] Installing Python dependencies..." -ForegroundColor Cyan
$ReqFile = Join-Path $AppDir "requirements.txt"
$Pip = Join-Path $VenvDir "Scripts\pip.exe"
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
$TaskUser = "$env:COMPUTERNAME\$env:USERNAME"

Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
Stop-Process -Name "python" -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

$Action = New-ScheduledTaskAction -Execute $VenvPython -Argument (Join-Path $AppDir "server.py") -WorkingDirectory $AppDir
$Trigger = New-ScheduledTaskTrigger -AtStartup
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
$Principal = New-ScheduledTaskPrincipal -UserId "$env:COMPUTERNAME\$env:USERNAME" -RunLevel Highest -LogonType Interactive
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
        Write-Host "  [!] Service start timeout — check logs: $AppDir\logs" -ForegroundColor Yellow
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
    $WebuiPip = Join-Path $WebuiVenv "Scripts\pip.exe"

    Write-Host "  Installing PyTorch (CPU only, no CUDA)..." -ForegroundColor Gray
    & $WebuiPip install torch --index-url https://download.pytorch.org/whl/cpu -q 2>&1 | Out-Null

    Write-Host "  Installing Open WebUI..." -ForegroundColor Gray
    & $WebuiPip install open-webui -q 2>&1 | Out-Null

    $WebuiBin = Join-Path $WebuiVenv "Scripts\open-webui.exe"
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
Write-Log "  Config:      $AppDir\.env"
Write-Log ""
Write-Log "  Commands (PowerShell Admin):"
Write-Log "    Start:    Start-ScheduledTask -TaskName 'GeometryAI Server'"
Write-Log "    Stop:     Stop-ScheduledTask -TaskName 'GeometryAI Server'"
Write-Log "    Logs:     Get-Content '$AppDir\logs\geometry_ai.log' -Tail 50"
Write-Log "    Uninstall: right-click uninstall.ps1 -> Run with PowerShell"
Write-Log ""
Write-Host "  Opening browser..." -ForegroundColor Cyan
Start-Sleep -Seconds 3
try { Start-Process "http://localhost:5000/admin" } catch {}
pause
