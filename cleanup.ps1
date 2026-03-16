# Kill all Python processes to ensure a clean start
Get-Process -Name "python" -ErrorAction SilentlyContinue | Stop-Process -Force

# Check for anything else on port 8000 (FastAPI)
$port = 8000
$processId = (Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue).OwningProcess
if ($processId) {
    Write-Host "Cleaning up process $processId on port $port"
    Stop-Process -Id $processId -Force
}

Write-Host "`n[CLEANUP COMPLETED] You can now run the system safely." -ForegroundColor Green
