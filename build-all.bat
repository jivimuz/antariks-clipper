@echo off
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
