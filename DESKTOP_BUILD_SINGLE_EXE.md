# Building Antariks Clipper Desktop App - Single Executable

This guide explains how to build Antariks Clipper as a **single executable file** (.exe) for Windows that contains both the Python backend and Electron frontend.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Development Setup](#development-setup)
- [Building the Application](#building-the-application)
- [Distribution](#distribution)
- [Troubleshooting](#troubleshooting)

## Overview

Antariks Clipper is packaged as a single executable desktop application that:
- ✅ Bundles Python backend using PyInstaller
- ✅ Uses Next.js static export for frontend
- ✅ Packages everything with Electron Builder
- ✅ Auto-starts and stops backend process
- ✅ Provides true "double-click and run" experience
- ✅ No Python or Node.js installation required

## Prerequisites

### System Requirements

- **Windows 10/11 (64-bit)** - For building Windows .exe
- **Node.js 18+** - For frontend and Electron
- **Python 3.8+** - For backend development and building
- **FFmpeg** - Required for video processing
  - Windows: Download from https://ffmpeg.org/download.html and add to PATH
  - macOS: `brew install ffmpeg`
  - Linux: `sudo apt-get install ffmpeg`

### Development Tools

- Git
- Text editor or IDE
- Terminal/Command prompt
- 5GB free disk space for build

## Development Setup

### 1. Clone and Install Dependencies

```bash
# Clone the repository
git clone https://github.com/jivimuz/antariks-clipper.git
cd antariks-clipper

# Install frontend dependencies (includes Electron)
cd frontend
npm install

# Install backend dependencies
cd ../backend
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install Python packages
pip install -r requirements_minimal.txt
pip install pyinstaller
```

### 2. Running in Development Mode

Development mode runs both the Next.js dev server and Electron, with the backend auto-starting:

```bash
cd frontend
npm run electron-dev
```

This command:
1. Starts the Next.js dev server on port 3000
2. Waits for the dev server to be ready
3. Launches Electron
4. Automatically starts the Python backend on port 8000
5. Opens DevTools for debugging

**Note**: The backend will automatically stop when you close the Electron window.

## Building the Application

### Option 1: Automated Build (Recommended)

From project root:

**Windows:**
```batch
build-all.bat
```

**macOS/Linux:**
```bash
./build-all.sh
```

This will:
1. Build the backend with PyInstaller (creates `antariks-backend.exe`)
2. Build the frontend with Next.js (static export to `out/`)
3. Package everything with Electron Builder (single installer .exe)

**Output**: `frontend/dist/AntariksClipper-1.0.0.exe`

### Option 2: Manual Build Steps

#### Step 1: Build Backend

```bash
cd backend

# Windows:
build.bat

# macOS/Linux:
./build.sh
```

This creates: `backend/dist/antariks-backend/` with `antariks-backend.exe`

#### Step 2: Build Frontend & Package

```bash
cd frontend

# Build Next.js static export
npm run build:frontend

# Package with Electron Builder
npm run build:electron
```

This creates: `frontend/dist/AntariksClipper-1.0.0.exe`

### Build Configuration

The build process is configured via:

**Backend**: `backend/build-backend.spec`
- PyInstaller configuration
- Hidden imports for all Python dependencies
- Console window disabled for production
- Output name: `antariks-backend.exe`

**Frontend**: `frontend/package.json` (build section)
- Electron Builder configuration
- ASAR packaging enabled
- Backend embedded as extraResources
- NSIS installer (one-click, single exe)

**Next.js**: `frontend/next.config.ts`
- Static HTML export enabled
- Images unoptimized for static serving
- API URL configured for local backend

## Distribution

### Windows Installer

**File**: `frontend/dist/AntariksClipper-1.0.0.exe`

**Size**: Approximately 500-800MB (includes all dependencies)

**What's included**:
- ✅ Electron runtime
- ✅ Next.js frontend (static HTML/CSS/JS)
- ✅ Python backend (PyInstaller bundle)
- ✅ All Python dependencies (FastAPI, Whisper, OpenCV, etc.)
- ✅ Node.js native modules

**Installation**:
- One-click NSIS installer
- Installs to user AppData (no admin required)
- Creates desktop shortcut
- Creates start menu shortcut
- Auto-launches on completion (optional)

**User Experience**:
1. Download `.exe` file
2. Double-click to install
3. Launch "Antariks Clipper" from desktop/start menu
4. Backend starts automatically in background
5. Frontend window opens
6. Ready to use!

### First Run

On first launch:
- App initializes (10-30 seconds)
- Whisper model downloads (~150MB) if not present
- Backend starts on port 8000
- Frontend loads from static files

## Architecture

### Single Executable Structure

```
AntariksClipper-1.0.0.exe (NSIS Installer)
└── Installed to: %LOCALAPPDATA%\Programs\antariks-clipper\
    ├── AntariksClipper.exe          # Main Electron executable
    ├── resources/
    │   ├── app.asar                 # Frontend code (ASAR archive)
    │   │   ├── out/                 # Next.js static export
    │   │   ├── electron/            # Electron main process
    │   │   └── node_modules/        # Node dependencies
    │   └── backend/                 # Backend executable bundle
    │       ├── antariks-backend.exe # PyInstaller executable
    │       └── _internal/           # Python dependencies
    └── (other Electron files)
```

### Runtime Flow

1. **User launches** `AntariksClipper.exe`
2. **Electron main process** starts (`electron/main.js`)
3. **Backend launcher** extracts and runs `antariks-backend.exe`
4. **Health check** waits for backend to be ready (port 8000)
5. **Browser window** loads static HTML from `out/index.html`
6. **Frontend** makes API calls to `http://127.0.0.1:8000`
7. **Backend** processes requests and returns data
8. **On close**: Backend process terminates automatically

## Configuration

### Environment Variables

**Production** (`frontend/.env.production`):
```
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

This ensures all API calls go to the local backend.

### Backend Configuration

The backend runs on `127.0.0.1:8000` (localhost only, not exposed to network).

To change the port, modify:
- `frontend/electron/backend-launcher.js` (port variable)
- `frontend/.env.production` (API URL)

## Testing

### Development Testing

- [ ] `npm run electron-dev` starts both services
- [ ] Frontend loads at localhost:3000
- [ ] Backend accessible at localhost:8000
- [ ] All features work (upload, YouTube, render)
- [ ] DevTools show no errors

### Production Build Testing

- [ ] `build-all.bat` completes without errors
- [ ] Single .exe file generated in `frontend/dist/`
- [ ] .exe installs successfully
- [ ] App launches after installation
- [ ] Backend starts automatically (check Task Manager)
- [ ] Frontend window opens and loads
- [ ] All API calls work
- [ ] Video processing works
- [ ] App closes cleanly (no zombie processes)

### Testing on Clean Machine

To properly test the installer:
1. Use a clean Windows VM or test machine
2. Ensure NO Python or Node.js is installed
3. Install the .exe
4. Launch the app
5. Test all features
6. Close and verify cleanup

## Troubleshooting

### Build Issues

#### Backend build fails

**Symptoms**: PyInstaller errors, missing modules

**Solutions**:
1. Activate virtual environment: `.venv\Scripts\activate`
2. Install dependencies: `pip install -r requirements_minimal.txt`
3. Install PyInstaller: `pip install pyinstaller`
4. Check `build-backend.spec` for missing hidden imports
5. Try: `pyinstaller build-backend.spec --clean --log-level DEBUG`

#### Frontend build fails

**Symptoms**: Next.js build errors, missing dependencies

**Solutions**:
1. Install dependencies: `npm install`
2. Clear cache: `rm -rf .next out`
3. Check Node.js version: `node --version` (should be 18+)
4. Try: `npm run build:frontend` separately

#### Electron Builder fails

**Symptoms**: Packaging errors, missing files

**Solutions**:
1. Ensure backend built: Check `backend/dist/antariks-backend/`
2. Ensure frontend built: Check `frontend/out/`
3. Check disk space (need ~5GB)
4. Try: `npm run pack` (without installer)

### Runtime Issues

#### Backend fails to start

**Symptoms**: Error dialog on launch, blank window

**Solutions**:
1. Check port 8000 availability: `netstat -ano | findstr :8000`
2. Check antivirus (may block `antariks-backend.exe`)
3. Check Windows Firewall
4. Run as administrator (if needed)
5. Check logs: Look in app's DevTools console

#### Frontend loads but API calls fail

**Symptoms**: Loading spinners, 404 errors, "Network Error"

**Solutions**:
1. Verify backend is running: Visit `http://127.0.0.1:8000/health`
2. Check CORS configuration in `backend/app.py`
3. Verify `NEXT_PUBLIC_API_URL` in `.env.production`
4. Open DevTools and check Network tab

#### Video processing fails

**Symptoms**: Jobs fail, render errors

**Solutions**:
1. Install FFmpeg on system
2. Add FFmpeg to PATH
3. For distribution, bundle FFmpeg in `frontend/resources/ffmpeg/`
4. Update backend to detect bundled FFmpeg

#### App won't close / Zombie processes

**Symptoms**: Process remains in Task Manager after closing

**Solutions**:
1. Check signal handlers in `backend/app.py`
2. Check backend launcher cleanup in `backend-launcher.js`
3. Kill manually: `taskkill /F /IM antariks-backend.exe`

### Distribution Issues

#### Large file size

**Expected**: 500-800MB is normal for Electron + Python + ML models

**To reduce**:
- Remove unnecessary Python packages
- Exclude test files
- Use UPX compression (already enabled)
- Consider on-demand model downloads

#### Windows Defender blocks installer

**Cause**: Unsigned executable

**Solutions**:
1. Code sign the application (requires certificate ~$100-300/year)
2. Users can bypass SmartScreen (right-click > "More info" > "Run anyway")
3. Submit to Microsoft for reputation building
4. Consider EV Code Signing for instant trust

#### Installer won't run

**Symptoms**: Double-click does nothing, permission errors

**Solutions**:
1. Right-click > "Run as administrator"
2. Check antivirus logs
3. Try portable version: `npm run dist:win -- --portable`
4. Disable antivirus temporarily for testing

## Advanced

### Custom Icons

Create icons in `frontend/build/`:
- `icon.ico` - Windows (256x256)
- `icon.icns` - macOS
- `icon.png` - Linux (512x512)

Use tools like:
- https://icoconvert.com/
- https://cloudconvert.com/png-to-ico
- Photoshop / GIMP

### Code Signing

For production releases, get a code signing certificate:

1. Purchase from CA (DigiCert, Sectigo, etc.)
2. Install certificate
3. Update `package.json`:
```json
{
  "win": {
    "certificateFile": "path/to/cert.pfx",
    "certificatePassword": "password"
  }
}
```
4. Build: `npm run dist:win`

### Auto-Update

Implement auto-updates using `electron-updater`:

1. Install: `npm install electron-updater`
2. Configure update server
3. Add update checking to `main.js`
4. Publish new releases

See: https://www.electron.build/auto-update

## Resources

- [Electron Documentation](https://www.electronjs.org/docs)
- [Electron Builder](https://www.electron.build/)
- [PyInstaller Manual](https://pyinstaller.org/en/stable/)
- [Next.js Static Export](https://nextjs.org/docs/app/building-your-application/deploying/static-exports)
- [NSIS Documentation](https://nsis.sourceforge.io/Docs/)

## Support

For issues and questions:
- GitHub Issues: https://github.com/jivimuz/antariks-clipper/issues
- Documentation: https://github.com/jivimuz/antariks-clipper
- Website: https://antariks.id

## License

Same as main project
