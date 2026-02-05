#!/bin/bash
# Validation script for Electron desktop app setup

echo "================================"
echo "Antariks Clipper Desktop Validation"
echo "================================"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check counter
PASS=0
FAIL=0

check() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $1"
        PASS=$((PASS + 1))
    else
        echo -e "${RED}✗${NC} $1"
        FAIL=$((FAIL + 1))
    fi
}

# 1. Check Node.js
echo "Checking dependencies..."
node --version > /dev/null 2>&1
check "Node.js installed"

# 2. Check Python
python3 --version > /dev/null 2>&1
check "Python 3 installed"

# 3. Check frontend dependencies
[ -d "frontend/node_modules" ]
check "Frontend dependencies installed (node_modules exists)"

# 4. Check Electron package
[ -d "frontend/node_modules/electron" ]
check "Electron installed"

# 5. Check backend venv
[ -d "backend/.venv" ]
check "Backend virtual environment exists"

# 6. Check Electron files
[ -f "frontend/electron/main.js" ]
check "Electron main.js exists"

[ -f "frontend/electron/preload.js" ]
check "Electron preload.js exists"

[ -f "frontend/electron/backend-launcher.js" ]
check "Backend launcher exists"

# 7. Check Next.js build
[ -d "frontend/.next" ]
check "Next.js production build exists"

# 8. Check configuration files
[ -f "frontend/.env.production" ]
check ".env.production exists"

[ -f "backend/build-backend.spec" ]
check "PyInstaller spec exists"

[ -f "backend/build.sh" ]
check "Backend build script exists"

# 9. Check documentation
[ -f "DESKTOP_BUILD.md" ]
check "Desktop build documentation exists"

echo ""
echo "================================"
echo "Summary: ${GREEN}${PASS} passed${NC}, ${RED}${FAIL} failed${NC}"
echo "================================"

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}All checks passed! Ready for development.${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Run 'cd frontend && npm run electron-dev' to test development mode"
    echo "  2. Run 'cd frontend && npm run dist' to build production app"
    exit 0
else
    echo -e "${YELLOW}Some checks failed. Please review the setup.${NC}"
    exit 1
fi
