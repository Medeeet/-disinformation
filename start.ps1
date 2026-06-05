# CyberShield KZ — однокомандный запуск (Windows PowerShell)
#   .\start.ps1                       — поднять сервер на http://localhost:8000
#   .\start.ps1 --port 9000           — любые флаги пробрасываются в uvicorn
#   $env:FORCE_INSTALL=1; .\start.ps1 — переустановить зависимости
#
# Если PowerShell ругается на политику выполнения, запусти так:
#   powershell -ExecutionPolicy Bypass -File .\start.ps1
# или один раз разреши скрипты для текущего пользователя:
#   Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

$venv   = "venv"
$marker = Join-Path $venv ".deps_installed"
$python = if ($env:PYTHON) { $env:PYTHON } else { "python" }

# 1. venv
if (-not (Test-Path "$venv\Scripts\Activate.ps1")) {
    Write-Host ">>> Создаю виртуальное окружение ($venv)..."
    & $python -m venv $venv
    if ($LASTEXITCODE -ne 0) { exit 1 }
}

# Активация
. "$venv\Scripts\Activate.ps1"

# 2. Зависимости
$needInstall = $env:FORCE_INSTALL -or (-not (Test-Path $marker))
if ($needInstall) {
    Write-Host ">>> Устанавливаю зависимости из requirements.txt..."
    pip install --upgrade pip -q
    pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) { exit 1 }
    New-Item -ItemType File -Path $marker -Force | Out-Null
}

# 3. .env (если есть)
if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]*)=(.*)$') {
            $key = $matches[1].Trim()
            $val = $matches[2].Trim().Trim('"').Trim("'")
            Set-Item -Path "env:$key" -Value $val
        }
    }
}

# 4. Дефолты
if (-not $env:DATABASE_URL) {
    $env:DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/cybershield"
}
$h = if ($env:HOST) { $env:HOST } else { "0.0.0.0" }
$p = if ($env:PORT) { $env:PORT } else { "8000" }

# 5. PostgreSQL через Docker (если установлен) — для локальной БД
$dbIsLocal = $env:DATABASE_URL -match "localhost|127\.0\.0\.1"
if (-not $env:SKIP_DOCKER -and (Test-Path "docker-compose.yml") -and $dbIsLocal `
        -and (Get-Command docker -ErrorAction SilentlyContinue)) {
    docker info 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host ">>> Поднимаю PostgreSQL через Docker..."
        docker compose up -d --wait
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[WARN] docker compose --wait не сработал, пробую без него..."
            docker compose up -d
            Start-Sleep -Seconds 5
        }
    } else {
        Write-Host "[WARN] Docker установлен, но демон не запущен. Запусти Docker Desktop."
    }
}

Write-Host ""
Write-Host "================================================================"
Write-Host "  CyberShield KZ"
Write-Host "  URL:      http://localhost:$p"
Write-Host "  Database: $env:DATABASE_URL"
Write-Host "================================================================"
Write-Host ""

uvicorn app.main:app --host $h --port $p @args
