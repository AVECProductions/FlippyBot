@echo off
REM FLIPPY Worker — Windows launcher
REM Run from the worker\ directory or from repo root.

cd /d "%~dp0"

REM Activate venv if present
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM Default: continuous mode, 30-minute interval
REM Pass --once for a single run, --interval N to change interval.
python main.py %*
