# Quick Build Guide - Single Executable

## Prerequisites ✅

- Windows 10/11 (64-bit)
- Node.js 18+
- Python 3.8+
- Git

## Quick Start (3 Steps)

### 1. Install Dependencies

```bash
# Install frontend dependencies
cd frontend
npm install

# Install backend dependencies
cd ../backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements_minimal.txt
pip install pyinstaller
```

### 2. (Optional) Add Icons

Create or add icons to `frontend/build/`:
- `icon.ico` - Windows (256x256)
- `icon.icns` - macOS
- `icon.png` - Linux (512x512)

**OR** Comment out icon paths in `frontend/package.json` to use defaults.

### 3. Build

```bash
# From project root
build-all.bat
```

Wait 5-10 minutes. Output: `frontend/dist/AntariksClipper-1.0.0.exe`

## What Gets Built

```
[1/3] Backend → backend/dist/antariks-backend/antariks-backend.exe
[2/3] Frontend → frontend/out/ (static HTML)
[3/3] Package → frontend/dist/AntariksClipper-1.0.0.exe
```

## Testing

```bash
# Install the .exe on a clean machine
# No Python or Node.js should be installed
# Double-click to install
# Launch from desktop shortcut
# Verify all features work
```

## Troubleshooting

**Backend build fails:**
- Activate venv: `.venv\Scripts\activate`
- Install PyInstaller: `pip install pyinstaller`

**Frontend build fails:**
- Install deps: `npm install`
- Check Node version: `node --version` (need 18+)

**Electron build fails:**
- Ensure backend built: Check `backend/dist/antariks-backend/`
- Ensure frontend built: Check `frontend/out/`
- Try: `npm run pack` (no installer)

**Icon warnings:**
- Comment out icon paths in `package.json`
- Or add placeholder icons

## Manual Steps

If automated build fails:

```bash
# Step 1: Build backend
cd backend
build.bat
cd ..

# Step 2: Build frontend  
cd frontend
npm run build:frontend

# Step 3: Package
npm run build:electron
```

## Build Time

- Backend: ~2-5 minutes
- Frontend: ~1-2 minutes
- Packaging: ~2-3 minutes
- **Total: ~5-10 minutes**

## Output Details

**File**: `frontend/dist/AntariksClipper-1.0.0.exe`
**Size**: ~500-800 MB
**Type**: NSIS one-click installer

**Contains**:
- Electron runtime (~150 MB)
- Next.js frontend (static)
- Python backend bundle (~200-400 MB)
- All dependencies

## Installation

User experience:
1. Download `.exe`
2. Double-click
3. One-click install (no config needed)
4. Desktop shortcut created
5. Launch and use immediately

## Documentation

- **Build Guide**: `DESKTOP_BUILD_SINGLE_EXE.md` (comprehensive)
- **User Guide**: `README_DESKTOP.md` (for end users)
- **Implementation**: `IMPLEMENTATION_NOTES.md` (technical details)

## Support

- Issues: https://github.com/jivimuz/antariks-clipper/issues
- Docs: See documentation files above
