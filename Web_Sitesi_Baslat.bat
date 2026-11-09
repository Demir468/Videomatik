@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Videomatik Web ve Mobil Sunucusu

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" web_app.py
) else if exist "%USERPROFILE%\.gemini\antigravity\scratch\video-downloader\.venv\Scripts\python.exe" (
    "%USERPROFILE%\.gemini\antigravity\scratch\video-downloader\.venv\Scripts\python.exe" web_app.py
) else (
    py web_app.py
)
pause
