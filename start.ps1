# CyberShield KZ — бір команданы іске қосу (Windows PowerShell)
#   .\start.ps1                       — серверді http://localhost:8000 мекенжайында көтеру
#   .\start.ps1 --port 9000           — кез келген жалаушалар uvicorn-ға беріледі
#   $env:FORCE_INSTALL=1; .\start.ps1 — тәуелділіктерді қайта орнату
#   $env:SKIP_DOCKER=1; .\start.ps1   — Docker-ді өткізіп жіберу
#
# PowerShell орындау саясатына шағымданса, былай іске қосыңыз:
#   powershell -ExecutionPolicy Bypass -File .\start.ps1
# немесе ағымдағы пайдаланушыға бір рет рұқсат беріңіз:
#   Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned

$ErrorActionPreference = "Stop"
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}
Set-Location -Path $PSScriptRoot

# Порт бос па, жоқ па тексеру
function Test-PortInUse([int]$Port) {
    try { $null = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction Stop; return $true }
    catch { return $false }
}
# Берілген порттан бастап бірінші бос портты табу
function Find-FreePort([int]$Start) {
    $p = $Start
    while ((Test-PortInUse $p) -and ($p -lt ($Start + 50))) { $p++ }
    return $p
}

$venv   = "venv"
$marker = Join-Path $venv ".deps_installed"
$python = if ($env:PYTHON) { $env:PYTHON } else { "python" }

# 1. Виртуалды орта
if (-not (Test-Path "$venv\Scripts\Activate.ps1")) {
    Write-Host ">>> Виртуалды орта жасалуда ($venv)..."
    & $python -m venv $venv
    if ($LASTEXITCODE -ne 0) { exit 1 }
}

# Активация
. "$venv\Scripts\Activate.ps1"

# 2. Тәуелділіктер
$needInstall = $env:FORCE_INSTALL -or (-not (Test-Path $marker))
if ($needInstall) {
    Write-Host ">>> requirements.txt тәуелділіктері орнатылуда..."
    pip install --upgrade pip -q
    pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) { exit 1 }
    New-Item -ItemType File -Path $marker -Force | Out-Null
}

# 3. .env (бар болса)
if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]*)=(.*)$') {
            $key = $matches[1].Trim()
            $val = $matches[2].Trim().Trim('"').Trim("'")
            Set-Item -Path "env:$key" -Value $val
        }
    }
}

# 4. Әдепкі мәндер
if (-not $env:DATABASE_URL) {
    $env:DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/cybershield"
}
$h = if ($env:HOST) { $env:HOST } else { "0.0.0.0" }
$desiredPort = if ($env:PORT) { [int]$env:PORT } else { 8000 }

# 5. Docker арқылы PostgreSQL (орнатылған болса) — жергілікті дерекқор үшін
$dbIsLocal = $env:DATABASE_URL -match "localhost|127\.0\.0\.1"
if (-not $env:SKIP_DOCKER -and (Test-Path "docker-compose.yml") -and $dbIsLocal `
        -and (Get-Command docker -ErrorAction SilentlyContinue)) {
    docker info 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        # Postgres үшін бос портты табу (5432 бос емес болса — келесісі)
        $desiredDbPort = if ($env:POSTGRES_PORT) { [int]$env:POSTGRES_PORT } else { 5432 }
        $dbPort = Find-FreePort $desiredDbPort
        if ($dbPort -ne $desiredDbPort) {
            Write-Host ">>> $desiredDbPort порты бос емес - Postgres $dbPort портында іске қосылады"
        }
        $env:POSTGRES_PORT = "$dbPort"
        # DATABASE_URL ішіндегі портты жаңасына ауыстыру
        $env:DATABASE_URL = $env:DATABASE_URL -replace '(@[^:/]+):\d+', ('${1}:' + $dbPort)

        Write-Host ">>> PostgreSQL Docker арқылы іске қосылуда (порт $dbPort)..."
        docker compose up -d --wait
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[ЕСКЕРТУ] docker compose --wait істемеді, --waitсіз сынап көремін..."
            docker compose up -d
            Start-Sleep -Seconds 5
        }
    } else {
        Write-Host "[ЕСКЕРТУ] Docker орнатылған, бірақ демоны іске қосылмаған. Docker Desktop-ты іске қосыңыз."
    }
}

# 6. Қосымша порты (бос емес болса — келесі бос порт)
$appPort = Find-FreePort $desiredPort
if ($appPort -ne $desiredPort) {
    Write-Host ">>> $desiredPort порты бос емес - қосымша $appPort портында іске қосылады"
}

Write-Host ""
Write-Host "================================================================"
Write-Host "  CyberShield KZ"
Write-Host "  Мекенжай:  http://localhost:$appPort"
Write-Host "  Дерекқор:  $env:DATABASE_URL"
Write-Host "================================================================"
Write-Host ""

uvicorn app.main:app --host $h --port $appPort @args
