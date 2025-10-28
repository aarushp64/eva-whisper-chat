# Eva AI Agent - Quick Setup Script for Windows
# Run this script to set up the development environment

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Eva AI Agent - Setup Script" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
Write-Host "Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found. Please install Python 3.9+" -ForegroundColor Red
    exit 1
}

# Check Node.js
Write-Host "Checking Node.js installation..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version
    Write-Host "✓ Node.js found: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Node.js not found. Please install Node.js 18+" -ForegroundColor Red
    exit 1
}

# Check Ollama
Write-Host "Checking Ollama installation..." -ForegroundColor Yellow
try {
    $ollamaVersion = ollama --version
    Write-Host "✓ Ollama found: $ollamaVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Ollama not found. Please install from https://ollama.ai" -ForegroundColor Red
    Write-Host "  After installing, run: ollama pull llama3.2" -ForegroundColor Yellow
    exit 1
}

# Setup Backend
Write-Host ""
Write-Host "Setting up Python backend..." -ForegroundColor Yellow
Set-Location "packages\backend\server"

# Create virtual environment
if (!(Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
.\venv\Scripts\Activate.ps1

# Install dependencies
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Download spacy model
Write-Host "Downloading Spacy model..." -ForegroundColor Yellow
python -m spacy download en_core_web_sm

# Create .env if it doesn't exist
if (!(Test-Path ".env")) {
    Write-Host "Creating .env file..." -ForegroundColor Yellow
    $envContent = @"
SECRET_KEY=dev_secret_key_change_in_production
JWT_SECRET_KEY=dev_jwt_secret_key_change_in_production
FLASK_ENV=development
DATABASE_URI=sqlite:///eva.db
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2
OLLAMA_HOST=http://localhost:11434
PORT=5000
"@
    $envContent | Out-File -FilePath ".env" -Encoding UTF8
    Write-Host "Created .env file" -ForegroundColor Green
}

# Go back to root
Set-Location "..\..\..\"

# Setup Frontend
Write-Host ""
Write-Host "Setting up frontend..." -ForegroundColor Yellow
Set-Location "packages\frontend"

# Install dependencies
Write-Host "Installing Node.js dependencies..." -ForegroundColor Yellow
npm install

# Create .env if it doesn't exist
if (!(Test-Path ".env")) {
    Write-Host "Creating frontend .env file..." -ForegroundColor Yellow
    $feEnv = @"
VITE_API_URL=http://localhost:5000
VITE_WS_URL=ws://localhost:5000
VITE_NODE_API_URL=http://localhost:8081
"@
    $feEnv | Out-File -FilePath ".env" -Encoding UTF8
    Write-Host "Created frontend .env file" -ForegroundColor Green
}

# Go back to root
Set-Location "..\.."

# Check if Ollama model is available
Write-Host ""
Write-Host "Checking Ollama models..." -ForegroundColor Yellow
$ollamaModels = ollama list
if ($ollamaModels -match "llama3.2") {
    Write-Host "✓ llama3.2 model found" -ForegroundColor Green
} else {
    Write-Host "⚠ llama3.2 model not found" -ForegroundColor Yellow
    Write-Host "  Pulling llama3.2 model (this may take a few minutes)..." -ForegroundColor Yellow
    ollama pull llama3.2
}

Write-Host ""
Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "To start the application:" -ForegroundColor Yellow
Write-Host "  1. Start backend:  .\scripts\start-backend.ps1" -ForegroundColor White
Write-Host "  2. Start frontend: .\scripts\start-frontend.ps1" -ForegroundColor White
Write-Host ""
Write-Host "Or run both with: .\scripts\start-all.ps1" -ForegroundColor White
Write-Host ""
