@echo off
REM Build script for both backend and frontend (Windows)

echo ========================================
echo Building Antariks Clipper - Full Build
echo ========================================

echo.
echo [1/6] Killing running processes...
taskkill /F /IM AntariksClipper.exe >nul 2>&1
taskkill /F /IM antariks-backend.exe >nul 2>&1

echo.
echo [2/6] Cleaning old builds...
cd backend
if exist dist rmdir /s /q dist 2>nul
if exist build rmdir /s /q build 2>nul
cd ..

cd frontend
if exist dist rmdir /s /q dist 2>nul
if exist out rmdir /s /q out 2>nul
if exist resources\backend rmdir /s /q resources\backend 2>nul
cd ..

echo.
echo [3/6] Building backend with PyInstaller...
cd backend
python -m PyInstaller build-backend.spec --noconfirm

if %errorlevel% neq 0 (
    echo.
    echo ❌ Backend build failed!
    echo.
    echo Troubleshooting:
    echo - Ensure Python dependencies: pip install -r requirements.txt
    echo - Verify PyInstaller: pip install pyinstaller
    echo - Verify ffmpeg: ffmpeg -version
    echo - Verify yt-dlp: yt-dlp --version
    echo.
    cd ..
    pause
    exit /b 1
)

echo.
echo [4/6] Copying backend to frontend resources...
if not exist ..\frontend\resources mkdir ..\frontend\resources
xcopy /E /I /Y dist\antariks-backend ..\frontend\resources\backend >nul 2>&1

cd ..

echo.
echo ✅ Backend build complete!
echo.
echo [5/6] Installing npm dependencies...
cd frontend
if not exist "node_modules" (
    call npm install
    if %errorlevel% neq 0 (
        echo ❌ npm install failed!
        cd ..
        pause
        exit /b 1
    )
)

echo.
echo [6/6] Building frontend with Electron...
call npm run build:electron

if %errorlevel% neq 0 (
    echo.
    echo ❌ Frontend build failed!
    cd ..
    pause
    exit /b 1
)

cd ..

echo.
echo ========================================
echo ✅✅✅ BUILD COMPLETE!
echo ========================================
echo.
echo Executable: frontend\dist\win-unpacked\AntariksClipper.exe
echo Installer: frontend\dist\AntariksClipper Setup.exe
echo.
echo Launching app...
timeout /t 2
start "" "frontend\dist\win-unpacked\AntariksClipper.exe"

echo.
pause
REM Build script for creating single executable Antariks Clipper

echo ========================================
echo Building Antariks Clipper Desktop App
echo ========================================

REM Check if we're in the project root
if not exist "backend" (
    echo Error: backend directory not found. Please run from project root.
    exit /b 1
)
if not exist "frontend" (
    echo Error: frontend directory not found. Please run from project root.
    exit /b 1
)

echo.
echo [1/3] Building Backend...
cd backend
call build.bat
if errorlevel 1 (
    echo Backend build failed!
    exit /b 1
)
cd ..

echo.
echo [2/3] Building Frontend...
cd frontend
call npm run build:frontend
if errorlevel 1 (
    echo Frontend build failed!
    exit /b 1
)

echo.
echo [3/3] Packaging Electron App...
call npm run build:electron
if errorlevel 1 (
    echo Electron build failed!
    exit /b 1
)

echo.
echo ========================================
echo Build Complete!
echo ========================================
echo Output: frontend\dist\AntariksClipper-1.0.0.exe
echo ========================================
cd ..
