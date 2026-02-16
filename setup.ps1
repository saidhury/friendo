# Smart Companion - Quick Setup Script (Windows PowerShell)
# Run: .\setup.ps1

Write-Host "Smart Companion - Quick Setup" -ForegroundColor Cyan
Write-Host "==============================" -ForegroundColor Cyan

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host "Creating .env file from template..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    
    # Generate encryption key
    Write-Host "Generating encryption key..." -ForegroundColor Yellow
    $key = python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" 2>$null
    
    if ($key) {
        (Get-Content ".env") -replace "^ENCRYPTION_KEY=.*$", "ENCRYPTION_KEY=$key" | Set-Content ".env"
        Write-Host "Encryption key generated!" -ForegroundColor Green
    } else {
        Write-Host "Could not generate key. Run: pip install cryptography" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "IMPORTANT: Edit .env and add your GEMINI_API_KEY" -ForegroundColor Yellow
    Write-Host "Get your key from: https://aistudio.google.com/" -ForegroundColor Gray
} else {
    Write-Host ".env file already exists" -ForegroundColor Green
}

Write-Host ""
Write-Host "Ready to deploy with Docker:" -ForegroundColor Cyan
Write-Host "  docker compose up --build" -ForegroundColor White
Write-Host ""
Write-Host "Or run locally:" -ForegroundColor Cyan
Write-Host "  Backend:  cd backend; pip install -r requirements.txt; uvicorn main:app --reload" -ForegroundColor White
Write-Host "  Frontend: cd frontend; npm install; npm run dev" -ForegroundColor White
