#!/bin/bash

echo "╔════════════════════════════════════════════════════════╗"
echo "║     Antariks Clipper - Installation Verification      ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track overall status
ERRORS=0

# Function to check command
check_command() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}✓${NC} $1 is installed"
        return 0
    else
        echo -e "${RED}✗${NC} $1 is NOT installed"
        ERRORS=$((ERRORS+1))
        return 1
    fi
}

# Function to check file exists
check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} Found: $1"
        return 0
    else
        echo -e "${RED}✗${NC} Missing: $1"
        ERRORS=$((ERRORS+1))
        return 1
    fi
}

# Function to check directory exists
check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✓${NC} Directory: $1"
        return 0
    else
        echo -e "${RED}✗${NC} Missing directory: $1"
        ERRORS=$((ERRORS+1))
        return 1
    fi
}

echo "1. Checking System Prerequisites..."
echo "───────────────────────────────────────────────────────"
check_command python3
check_command node
check_command npm
check_command ffmpeg
echo ""

echo "2. Checking Backend Files..."
echo "───────────────────────────────────────────────────────"
check_file "backend/app.py"
check_file "backend/db.py"
check_file "backend/config.py"
check_file "backend/requirements.txt"
check_file "backend/README.md"
check_dir "backend/services"
check_file "backend/services/downloader.py"
check_file "backend/services/ffmpeg.py"
check_file "backend/services/transcribe.py"
check_file "backend/services/highlight.py"
check_file "backend/services/thumbnails.py"
check_file "backend/services/face_track.py"
check_file "backend/services/reframe.py"
check_file "backend/services/render.py"
check_file "backend/services/jobs.py"
echo ""

echo "3. Checking Frontend Files..."
echo "───────────────────────────────────────────────────────"
check_file "frontend/package.json"
check_file "frontend/app/page.tsx"
check_file "frontend/app/layout.tsx"
check_file "frontend/app/jobs/page.tsx"
check_file "frontend/app/jobs/[id]/page.tsx"
check_file "frontend/README.md"
echo ""

echo "4. Checking Documentation..."
echo "───────────────────────────────────────────────────────"
check_file "README.md"
check_file "ARCHITECTURE.md"
check_file "QUICKSTART.md"
check_file ".gitignore"
echo ""

echo "5. Checking Backend Structure..."
echo "───────────────────────────────────────────────────────"
check_dir "backend/data"
check_dir "backend/data/raw"
check_dir "backend/data/normalized"
check_dir "backend/data/transcripts"
check_dir "backend/data/thumbnails"
check_dir "backend/data/renders"
echo ""

echo "╔════════════════════════════════════════════════════════╗"
if [ $ERRORS -eq 0 ]; then
    echo -e "║  ${GREEN}✓ Installation Verification: PASSED${NC}               ║"
    echo "╚════════════════════════════════════════════════════════╝"
    echo ""
    echo -e "${GREEN}All checks passed!${NC} Your installation is complete."
    echo ""
    echo "Next steps:"
    echo "  1. Read QUICKSTART.md for setup instructions"
    echo "  2. Install backend dependencies: cd backend && pip install -r requirements.txt"
    echo "  3. Install frontend dependencies: cd frontend && npm install"
    echo "  4. Start the application!"
    exit 0
else
    echo -e "║  ${RED}✗ Installation Verification: FAILED${NC}               ║"
    echo "╚════════════════════════════════════════════════════════╝"
    echo ""
    echo -e "${RED}Found $ERRORS error(s)${NC}"
    echo "Please check the errors above and ensure all files are present."
    exit 1
fi
