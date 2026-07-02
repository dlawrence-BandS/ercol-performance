@echo off
title Ercol Performance — Data Refresh
color 0A
echo.
echo  =========================================
echo   Ercol Performance Dashboard — Refresh
echo  =========================================
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

REM ── Run refresh script ────────────────────────────────────────────────────
cd /d "%~dp0.."
%PYTHON% scripts\ercol_refresh.py

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
