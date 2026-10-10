# ResAI PowerShell Setup Script
Write-Host "Setting up ResAI environment..." -ForegroundColor Cyan

# 1. Virtual environment setup
if (-not (Test-Path ".venv")) {
    Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
}

# 2. Add backend directory to Python path
$backendPath = Join-Path (Get-Location) "backend"
Set-Content -Path ".venv\Lib\site-packages\backend.pth" -Value $backendPath

# 3. Install backend dependencies
Write-Host "Installing backend Python packages..." -ForegroundColor Yellow
.\.venv\Scripts\pip.exe install -r backend\requirements.txt

# 3. Install frontend dependencies
Write-Host "Installing frontend npm packages..." -ForegroundColor Yellow
Set-Location frontend
npm install
Set-Location ..

Write-Host "ResAI setup completed successfully!" -ForegroundColor Green
Write-Host "To start backend: .\.venv\Scripts\uvicorn.exe app.main:app --reload --port 8000 (from backend/ or with PYTHONPATH=backend)"
Write-Host "To start frontend: cd frontend && npm run dev"
