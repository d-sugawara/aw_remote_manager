@echo off
chcp 65001 > nul
echo ========================================
echo  AW Remote Manager - Build Script
echo ========================================

echo [1/3] Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: pip install failed
    pause
    exit /b 1
)

echo [2/3] Building exe...
python -m PyInstaller ^
    --onefile ^
    --noconsole ^
    --name AW_RemoteManager ^
    --hidden-import=win32timezone ^
    --hidden-import=win32api ^
    --hidden-import=win32con ^
    --hidden-import=win32gui ^
    --hidden-import=pystray._win32 ^
    --hidden-import=win10toast ^
    --hidden-import=google.auth.transport.requests ^
    --hidden-import=google_auth_oauthlib.flow ^
    --hidden-import=PIL._imaging ^
    --collect-all google_auth_oauthlib ^
    --collect-all google.auth ^
    main.py

if %errorlevel% neq 0 (
    echo ERROR: PyInstaller build failed
    pause
    exit /b 1
)

echo [3/3] Copying config file...
if not exist "dist\config.json" (
    copy config.json dist\config.json
    echo Copied config.json to dist folder
)

echo.
echo ========================================
echo  Build Complete!
echo  Run: dist\AW_RemoteManager.exe
echo  Edit dist\config.json before running:
echo    - base_url: Server URL
echo    - google_client_id: Google OAuth Client ID
echo    - google_client_secret: Google OAuth Client Secret
echo ========================================
pause
