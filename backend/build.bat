@echo off
REM Build script for backend using PyInstaller (Windows)

echo ================================
echo Building Antariks Clipper Backend
echo ================================

REM Check if we're in the backend directory
if not exist "app.py" (
    echo Error: app.py not found. Please run this script from the backend directory.
    exit /b 1
)

REM Check if virtual environment exists
if not exist ".venv" (
    echo Warning: Virtual environment not found. Creating one...
    python -m venv .venv
)

REM Activate virtual environment
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
pip install -r requirements_minimal.txt 2>nul

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
