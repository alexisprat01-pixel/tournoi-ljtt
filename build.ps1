# Build Top12.exe — single-file Windows executable
# Usage: .\build.ps1

$ErrorActionPreference = 'Stop'

Write-Host "=== Top12 build ===" -ForegroundColor Red

# 1. Ensure venv exists
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Cyan
    python -m venv .venv
}

# 2. Activate it
. .\.venv\Scripts\Activate.ps1

# 3. Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Cyan
pip install --upgrade pip | Out-Null
pip install -r requirements.txt

# 4. Clean previous build
if (Test-Path "build") { Remove-Item -Recurse -Force build }
if (Test-Path "dist")  { Remove-Item -Recurse -Force dist }

# 5. Run PyInstaller
Write-Host "Packaging with PyInstaller..." -ForegroundColor Cyan
pyinstaller --noconfirm --clean top12.spec

# 6. Report
$exe = Join-Path -Path (Get-Location) -ChildPath "dist\Top12.exe"
if (Test-Path $exe) {
    $size = [Math]::Round((Get-Item $exe).Length / 1MB, 1)
    Write-Host ""
    Write-Host "=== Build OK ===" -ForegroundColor Green
    Write-Host "Executable: $exe" -ForegroundColor Green
    Write-Host "Taille    : $size Mo" -ForegroundColor Green
    Write-Host ""
    Write-Host "Copie ce .exe sur n'importe quel PC Windows, double-clic, c'est parti." -ForegroundColor Yellow
} else {
    Write-Host "Build a échoué (pas de dist\Top12.exe)" -ForegroundColor Red
    exit 1
}
