@echo off
title Ercol Performance — Data Refresh
color 0A
echo.
echo  =========================================
echo   Ercol Performance Dashboard — Refresh
echo  =========================================
echo.

REM ── Get the folder this bat file lives in ────────────────────────────────
set REPO_DIR=%~dp0
REM Remove trailing backslash
if "%REPO_DIR:~-1%"=="\" set REPO_DIR=%REPO_DIR:~0,-1%

echo  Repo folder: %REPO_DIR%
echo.

REM ── Find Python ──────────────────────────────────────────────────────────
set PYTHON=
where python >nul 2>&1 && set PYTHON=python
if "%PYTHON%"=="" where python3 >nul 2>&1 && set PYTHON=python3
if "%PYTHON%"=="" (
    echo  ERROR: Python not found. Please install Python and try again.
    pause
    exit /b 1
)

REM ── Run refresh script from repo root ────────────────────────────────────
cd /d "%REPO_DIR%"
%PYTHON% "%REPO_DIR%\scripts\ercol_refresh.py"

echo.
if %ERRORLEVEL% EQU 0 (
    echo  =========================================
    echo   Done! Open the dashboard to see updates.
    echo  =========================================
) else (
    echo  =========================================
    echo   Something went wrong. Check output above.
    echo  =========================================
)
echo.
pause
