#!/bin/bash
set -e

echo "========================================"
echo "Building Antariks Clipper Desktop App"
echo "========================================"

# Check if we're in the project root
if [ ! -d "backend" ]; then
    echo "Error: backend directory not found. Please run from project root."
    exit 1
fi
if [ ! -d "frontend" ]; then
    echo "Error: frontend directory not found. Please run from project root."
    exit 1
fi

echo ""
echo "[1/3] Building Backend..."
cd backend
chmod +x build.sh
./build.sh
cd ..

echo ""
echo "[2/3] Building Frontend..."
cd frontend
npm run build:frontend

echo ""
echo "[3/3] Packaging Electron App..."
npm run build:electron

echo ""
echo "========================================"
echo "Build Complete!"
echo "========================================"
echo "Output: frontend/dist/"
echo "========================================"
