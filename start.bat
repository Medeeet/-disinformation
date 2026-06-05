@echo off
chcp 65001 >nul 2>&1
REM CyberShield KZ - бір команданы іске қосу (Windows)
REM   start.bat                        - серверді http://localhost:8000 мекенжайында көтеру
REM   start.bat --port 9000            - кез келген жалаушалар uvicorn-ға беріледі
REM   set FORCE_INSTALL=1 && start.bat - тәуелділіктерді қайта орнату
REM   set SKIP_DOCKER=1 && start.bat   - Docker-ді өткізіп жіберу

setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

set "PY=python"
set "VENV=venv"
set "MARKER=%VENV%\.deps_installed"

REM 1. Виртуалды орта
if not exist "%VENV%\Scripts\activate.bat" (
    echo ^>^>^> Виртуалды орта жасалуда ^(%VENV%^)...
    %PY% -m venv "%VENV%"
    if errorlevel 1 goto :error
)

call "%VENV%\Scripts\activate.bat"
if errorlevel 1 goto :error

REM 2. Тәуелділіктер (маркер жоқ болса немесе FORCE_INSTALL қойылса)
set "NEED_INSTALL="
if defined FORCE_INSTALL set "NEED_INSTALL=1"
if not exist "%MARKER%" set "NEED_INSTALL=1"

if defined NEED_INSTALL (
    echo ^>^>^> requirements.txt тәуелділіктері орнатылуда...
    pip install --upgrade pip -q
    pip install -r requirements.txt
    if errorlevel 1 goto :error
    type nul > "%MARKER%"
)

REM 3. .env (бар болса) — қарапайым KEY=VALUE талдаушы
if exist ".env" (
    for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
        set "_K=%%A"
        if not "!_K!"=="" if not "!_K:~0,1!"=="#" set "%%A=%%B"
    )
)

REM 4. Әдепкі DATABASE_URL
if not defined DATABASE_URL set "DATABASE_URL=postgresql://postgres:postgres@localhost:5432/cybershield"
if not defined HOST set "HOST=0.0.0.0"
if not defined PORT set "PORT=8000"

REM 5. Docker арқылы PostgreSQL (орнатылған болса) — жергілікті дерекқор үшін
if not defined SKIP_DOCKER if exist "docker-compose.yml" (
    where docker >nul 2>&1
    if not errorlevel 1 (
        echo !DATABASE_URL! | findstr /C:"localhost" /C:"127.0.0.1" >nul
        if not errorlevel 1 (
            docker info >nul 2>&1
            if not errorlevel 1 (
                REM Postgres үшін бос портты табу
                set "DESIRED_DB_PORT=5432"
                if defined POSTGRES_PORT set "DESIRED_DB_PORT=!POSTGRES_PORT!"
                call :find_free_port !DESIRED_DB_PORT!
                set "POSTGRES_PORT=!FREE_PORT!"
                if not "!FREE_PORT!"=="!DESIRED_DB_PORT!" echo ^>^>^> !DESIRED_DB_PORT! порты бос емес - Postgres !FREE_PORT! портында іске қосылады
                REM DATABASE_URL ішіндегі портты жаңасына ауыстыру (python арқылы)
                for /f "delims=" %%U in ('python -c "import os,re,sys;print(re.sub(r'(@[^:/]+):\d+', r'\g<1>:'+sys.argv[1], os.environ['DATABASE_URL']))" !FREE_PORT!') do set "DATABASE_URL=%%U"
                echo ^>^>^> PostgreSQL Docker арқылы іске қосылуда ^(порт !FREE_PORT!^)...
                docker compose up -d --wait
                if errorlevel 1 (
                    echo [ЕСКЕРТУ] docker compose --wait істемеді, --waitсіз сынап көремін...
                    docker compose up -d
                    timeout /t 5 /nobreak >nul
                )
            ) else (
                echo [ЕСКЕРТУ] Docker орнатылған, бірақ демоны іске қосылмаған. Docker Desktop-ты іске қосыңыз.
            )
        )
    )
)

REM 6. Қосымша порты (бос емес болса — келесі бос порт)
call :find_free_port %PORT%
set "APP_PORT=!FREE_PORT!"
if not "!APP_PORT!"=="%PORT%" echo ^>^>^> %PORT% порты бос емес - қосымша !APP_PORT! портында іске қосылады

echo.
echo ================================================================
echo   CyberShield KZ
echo   Мекенжай:  http://localhost:!APP_PORT!
echo   Дерекқор:  !DATABASE_URL!
echo ================================================================
echo.

uvicorn app.main:app --host %HOST% --port !APP_PORT! %*
goto :end

REM ── Көмекші: берілген порттан бастап бірінші бос портты табу ──
REM кіріс: %1 — бастапқы порт; шығыс: FREE_PORT айнымалысы
:find_free_port
set "FREE_PORT=%~1"
:ffp_loop
netstat -an | findstr /C:":!FREE_PORT! " >nul 2>&1
if not errorlevel 1 (
    set /a "FREE_PORT=FREE_PORT+1"
    goto ffp_loop
)
exit /b 0

:error
echo.
echo [ҚАТЕ] Іске қосу кезінде қате. Жоғарыдағы хабарды қараңыз.
exit /b 1

:end
endlocal
