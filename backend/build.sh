#!/bin/bash
# Build script for backend using PyInstaller

set -e  # Exit on error

echo "================================"
echo "Building Antariks Clipper Backend"
echo "================================"

# Check if we're in the backend directory
if [ ! -f "app.py" ]; then
    echo "Error: app.py not found. Please run this script from the backend directory."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Warning: Virtual environment not found. Creating one..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    source .venv/Scripts/activate
else
    # Unix-like
    source .venv/bin/activate
fi

# Install/upgrade PyInstaller
echo "Installing PyInstaller..."
pip install --upgrade pyinstaller

# Install dependencies if not already installed
echo "Installing dependencies..."
pip install -r requirements_minimal.txt 2>/dev/null || echo "Some dependencies may already be installed"

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build dist __pycache__

# Build with PyInstaller
echo "Building with PyInstaller..."
pyinstaller build-backend.spec --clean

echo ""
echo "================================"
echo "Build complete!"
echo "================================"
echo "Executable location: dist/app/"
echo ""
echo "To test the build:"
echo "  cd dist/app"
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    echo "  ./app.exe"
else
    echo "  ./app"
fi
echo ""
echo "Note: You may need to bundle FFmpeg binaries separately for Windows distribution."
