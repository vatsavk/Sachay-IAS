param(
    [string]$VenvPath = ".venv",
    [int]$Port = 8000
)

Write-Host "Creating venv at $VenvPath (if missing)"
if (-not (Test-Path $VenvPath)) {
    python -m venv $VenvPath
}

& $VenvPath\Scripts\python.exe -m pip install --upgrade pip
& $VenvPath\Scripts\python.exe -m pip install -r requirements.txt

Write-Host "Starting vercel_demo..."
$env:DEBUG_ALLOW = '1'
$env:ADMIN_PASSWORD = 'local-test-pass'
Start-Process -FilePath $VenvPath\Scripts\python.exe -ArgumentList '-m', 'uvicorn', 'api_server:app', '--port', "$Port" -NoNewWindow

Write-Host "Waiting for server to start on port $Port (max 30s)"
$ok = $false
for ($i=0; $i -lt 30; $i++) {
    try {
        $r = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:$Port/health" -TimeoutSec 2 -ErrorAction Stop
        if ($r.StatusCode -eq 200) { $ok = $true; break }
    } catch { Start-Sleep -Seconds 1 }
}

if ($ok) {
    Write-Host "Health OK:"
    Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:$Port/health" | Select-Object -ExpandProperty Content
    Write-Host "Debug status (may require DEBUG_ALLOW=1):"
    try { Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:$Port/debug/status" -TimeoutSec 5 | Select-Object -ExpandProperty Content } catch { Write-Host "debug unavailable" }
} else {
    Write-Host "Server did not start within timeout. Check logs or run run_uvicorn.py manually."
}
