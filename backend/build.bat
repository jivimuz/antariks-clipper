@echo off
REM Build script for backend + frontend (Windows)

echo ========================================
echo Building Antariks Clipper Backend
echo ========================================

REM Check if we're in the backend directory
if not exist "app.py" (
    echo Error: app.py not found. Please run this script from the backend directory.
    exit /b 1
)

echo.
echo [1/5] Killing running processes...
taskkill /F /IM AntariksClipper.exe >nul 2>&1
taskkill /F /IM antariks-backend.exe >nul 2>&1

echo.
echo [2/5] Cleaning old build...
if exist dist rmdir /s /q dist 2>nul
if exist build rmdir /s /q build 2>nul
if exist ..\frontend\dist rmdir /s /q ..\frontend\dist 2>nul
if exist ..\frontend\resources\backend rmdir /s /q ..\frontend\resources\backend 2>nul

echo.
echo [3/5] Building backend with PyInstaller...
python -m PyInstaller build-backend.spec --noconfirm

if %errorlevel% neq 0 (
    echo.
    echo ❌ Backend build failed!
    echo.
    echo Troubleshooting:
    echo - Ensure all Python dependencies are installed: pip install -r requirements.txt
    echo - Check if PyInstaller is installed: pip install pyinstaller
    echo - Verify ffmpeg is installed: ffmpeg -version
    echo - Verify yt-dlp is installed: yt-dlp --version
    echo.
    pause
    exit /b 1
)

echo.
echo [4/5] Copying to frontend resources...
if not exist ..\frontend\resources mkdir ..\frontend\resources
xcopy /E /I /Y dist\antariks-backend ..\frontend\resources\backend >nul 2>&1

if %errorlevel% neq 0 (
    echo ⚠️  Warning: Failed to copy backend files
)

echo.
echo ✅ Backend build complete!
echo.
echo ========================================
echo Building Antariks Frontend
echo ========================================

cd ..\frontend

REM Check Node modules
if not exist "node_modules" (
    echo Installing npm dependencies...
    call npm install
    if %errorlevel% neq 0 (
        echo ❌ npm install failed!
        cd ..\backend
        pause
        exit /b 1
    )
)

echo.
echo [5/5] Building frontend with Electron...
call npm run build:electron

if %errorlevel% neq 0 (
    echo.
    echo ❌ Frontend build failed!
    cd ..\backend
    pause
    exit /b 1
)

cd ..\backend

echo.
echo ========================================
echo ✅✅✅ BUILD COMPLETE!
echo ========================================
echo.
echo Executable: frontend\dist\win-unpacked\AntariksClipper.exe
echo.
echo Launching app...
timeout /t 2
start "" "frontend\dist\win-unpacked\AntariksClipper.exe"

echo.
pause
echo Activating virtual environment...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo Error: Failed to activate virtual environment
    exit /b 1
)

REM Install/upgrade PyInstaller
echo Installing PyInstaller...
pip install --upgrade pyinstaller
if errorlevel 1 (
    echo Error: Failed to install PyInstaller
    exit /b 1
)

REM Install dependencies if not already installed
echo Installing dependencies...
if exist "requirements.txt" (
    pip install -r requirements.txt
) else (
    pip install -r requirements_minimal.txt 2>nul
)

REM Clean previous builds
echo Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__

REM Build with PyInstaller
echo Building with PyInstaller...
pyinstaller build-backend.spec --clean
if errorlevel 1 (
    echo Error: PyInstaller build failed
    exit /b 1
)

echo.
echo ================================
echo Build complete!
echo ================================
echo Executable location: dist\antariks-backend\
echo.
echo To test the build:
echo   cd dist\antariks-backend
echo   antariks-backend.exe
echo.
echo Note: You may need to bundle FFmpeg binaries separately for Windows distribution.
