<#
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
