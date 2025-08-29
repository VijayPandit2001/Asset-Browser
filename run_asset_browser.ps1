# PowerShell script to run Asset Browser

Write-Host "Starting Asset Browser..." -ForegroundColor Green

# Check if virtual environment exists
if (Test-Path ".venv\Scripts\python.exe") {
    Write-Host "Using virtual environment..." -ForegroundColor Yellow
    & ".venv\Scripts\python.exe" main.py $args
} else {
    Write-Host "Virtual environment not found. Using system Python..." -ForegroundColor Yellow
    & python main.py $args
}

Write-Host "Press any key to continue..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
