@echo off
chcp 65001 >nul
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" app.py
) else if exist "%USERPROFILE%\.gemini\antigravity\scratch\video-downloader\.venv\Scripts\python.exe" (
    "%USERPROFILE%\.gemini\antigravity\scratch\video-downloader\.venv\Scripts\python.exe" app.py
) else (
    echo Sanal ortam (.venv) bulunamadi, ilk kurulum yapiliyor...
    py -m venv .venv
    ".venv\Scripts\pip.exe" install -r requirements.txt
    ".venv\Scripts\python.exe" app.py
)
if %errorlevel% neq 0 pause
