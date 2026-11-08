@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Videomatik Kurulum ve Masaustu Kisayol Olusturucu

echo ========================================================
echo   Videomatik - Kurulum ve Masaustu Kisayol Olusturucu
echo ========================================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [1/3] Python sanal ortami (.venv) olusturuluyor...
    py -m venv .venv
    if %errorlevel% neq 0 (
        python -m venv .venv
    )
    echo [2/3] Gerekli kutuphaneler yukleniyor, lutfen bekleyin...
    ".venv\Scripts\pip.exe" install -r requirements.txt
) else (
    echo [1/3] Kurulum zaten mevcut.
)

echo [3/3] Masaustune ikonlu "Videomatik" uygulama kisayolu ekleniyor...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$desktop = [Environment]::GetFolderPath('Desktop'); $s = (New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path $desktop 'Videomatik.lnk')); $s.TargetPath = '%~dp0.venv\Scripts\pythonw.exe'; $s.Arguments = '\"%~dp0app.py\"'; $s.WorkingDirectory = '%~dp0'; $s.IconLocation = '%~dp0assets\icon.ico'; $s.Description = 'Videomatik - Evrensel Video ve Ses Indirici'; $s.Save()"

echo.
echo Tamamlandi! Masaustunuzdeki "Videomatik" kisayolundan uygulamayi her zaman acabilirsiniz.
echo Uygulama simdi baslatiliyor...
start "" ".venv\Scripts\pythonw.exe" "app.py"
timeout /t 3 >nul
