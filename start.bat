@echo off
REM CyberShield KZ - однокомандный запуск (Windows)
REM   start.bat                       - поднять сервер на http://localhost:8000
REM   start.bat --port 9000           - любые флаги пробрасываются в uvicorn
REM   set FORCE_INSTALL=1 && start.bat - переустановить зависимости

setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

set "PY=python"
set "VENV=venv"
set "MARKER=%VENV%\.deps_installed"

REM 1. venv
if not exist "%VENV%\Scripts\activate.bat" (
    echo ^>^>^> Создаю виртуальное окружение ^(%VENV%^)...
    %PY% -m venv "%VENV%"
    if errorlevel 1 goto :error
)

call "%VENV%\Scripts\activate.bat"
if errorlevel 1 goto :error

REM 2. Зависимости (ставим если маркера нет или есть FORCE_INSTALL)
set "NEED_INSTALL="
if defined FORCE_INSTALL set "NEED_INSTALL=1"
if not exist "%MARKER%" set "NEED_INSTALL=1"

if defined NEED_INSTALL (
    echo ^>^>^> Устанавливаю зависимости из requirements.txt...
    pip install --upgrade pip -q
    pip install -r requirements.txt
    if errorlevel 1 goto :error
    type nul > "%MARKER%"
)

REM 3. .env (если есть) — простой парсер KEY=VALUE
if exist ".env" (
    for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
        set "_K=%%A"
        if not "!_K!"=="" if not "!_K:~0,1!"=="#" set "%%A=%%B"
    )
)

REM 4. Дефолтный DATABASE_URL
if not defined DATABASE_URL set "DATABASE_URL=postgresql://postgres:postgres@localhost:5432/cybershield"
if not defined HOST set "HOST=0.0.0.0"
if not defined PORT set "PORT=8000"

echo.
echo ================================================================
echo   CyberShield KZ
echo   URL:      http://localhost:%PORT%
echo   Database: %DATABASE_URL%
echo ================================================================
echo.

uvicorn app.main:app --host %HOST% --port %PORT% %*
goto :eof

:error
echo.
echo [ERROR] Ошибка при запуске. См. сообщение выше.
exit /b 1
