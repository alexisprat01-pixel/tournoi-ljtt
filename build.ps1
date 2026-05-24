# Build Top12.exe — single-file Windows executable
# Usage:
#   .\build.ps1            (silencieux, juste le résultat)
#   .\build.ps1 -Verbose   (affiche tout le log PyInstaller)
#
# En cas d'échec, le log complet est dans build.log

param([switch]$Verbose)

$ErrorActionPreference = 'Stop'
$logFile = "build.log"

Write-Host "=== Top12 build ===" -ForegroundColor Red

# 1. Ensure venv exists
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Cyan
    python -m venv .venv | Out-Null
}

# 2. Activate it
. .\.venv\Scripts\Activate.ps1

# 3. Install dependencies (silent unless verbose)
if ($Verbose) {
    pip install --upgrade pip
    pip install -r requirements.txt
} else {
    pip install --upgrade pip 2>&1 | Out-Null
    pip install -r requirements.txt 2>&1 | Out-File $logFile -Encoding utf8
}

# 4. Clean previous build
if (Test-Path "build") { Remove-Item -Recurse -Force build }
if (Test-Path "dist")  { Remove-Item -Recurse -Force dist }

# 5. Run PyInstaller (silent unless verbose)
Write-Host "Packaging..." -ForegroundColor Cyan
if ($Verbose) {
    pyinstaller --noconfirm --clean top12.spec
    $exitCode = $LASTEXITCODE
} else {
    pyinstaller --noconfirm --clean top12.spec 2>&1 | Out-File $logFile -Encoding utf8 -Append
    $exitCode = $LASTEXITCODE
}

# 6. Report
$exe = Join-Path -Path (Get-Location) -ChildPath "dist\Top12.exe"
if ($exitCode -eq 0 -and (Test-Path $exe)) {
    $size = [Math]::Round((Get-Item $exe).Length / 1MB, 1)
    Write-Host "OK -> $exe  ($size Mo)" -ForegroundColor Green
} else {
    Write-Host "Build FAILED (exit $exitCode)" -ForegroundColor Red
    Write-Host "Voir $logFile pour les détails (ou relancer avec -Verbose)" -ForegroundColor Yellow
    exit 1
}
