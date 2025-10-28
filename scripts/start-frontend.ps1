# Start Eva Frontend

Write-Host "Starting Eva Frontend..." -ForegroundColor Cyan

Set-Location "packages\frontend"

Write-Host "Frontend running on http://localhost:5173" -ForegroundColor Green
npm run dev
