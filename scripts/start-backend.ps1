# Start Eva Backend

Write-Host "Starting Eva Backend..." -ForegroundColor Cyan

Set-Location "packages\backend\server"

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Start Flask app
Write-Host "Backend running on http://localhost:5000" -ForegroundColor Green
python app.py
