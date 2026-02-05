# Desktop Application Build Guide

This guide explains how to build and distribute Antariks Clipper as a standalone desktop application using Electron.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Development Setup](#development-setup)
- [Building the Application](#building-the-application)
- [Distribution](#distribution)
- [Troubleshooting](#troubleshooting)

## Overview

Antariks Clipper is packaged as an Electron desktop application that:
- Automatically starts and stops the Python backend
- Bundles the Next.js frontend as static files
- Provides a native desktop experience
- Supports Windows, macOS, and Linux

## Prerequisites

### System Requirements

- **Node.js 18+** - For frontend and Electron
- **Python 3.8+** - For backend
- **FFmpeg** - Required for video processing
  - Windows: Download from https://ffmpeg.org/download.html
  - macOS: `brew install ffmpeg`
  - Linux: `sudo apt-get install ffmpeg`

### Development Tools

- Git
- Text editor or IDE
- Terminal/Command prompt

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

### 3. Development Workflow

When developing:
- Frontend changes: Next.js hot-reload works automatically
- Backend changes: Restart the Electron app to pick up backend changes
- Electron main process changes: Restart the Electron app

To restart:
1. Close the Electron window
2. Run `npm run electron-dev` again

## Building the Application

### 1. Prepare Application Icons

Before building, create application icons:

```bash
cd frontend/build
```

Required icons:
- **icon.ico** - Windows (256x256 pixels)
- **icon.icns** - macOS icon bundle
- **icon.png** - Linux (512x512 pixels)

See `frontend/build/README.md` for icon creation instructions.

### 2. Build Frontend for Production

```bash
cd frontend
npm run export
```

This creates a static export in `frontend/out/` directory.

### 3. Build Desktop Application

#### Build for Current Platform

```bash
cd frontend
npm run dist
```

This will:
1. Build the Next.js static export
2. Package with Electron
3. Create an installer in `frontend/dist/`

#### Build for Specific Platform

```bash
# Windows
npm run dist:win

# macOS
npm run dist:mac

# Linux
npm run dist:linux
```

#### Test Without Creating Installer

To test the packaged app without creating an installer:

```bash
npm run pack
```

This creates an unpacked version in `frontend/dist/[platform]-unpacked/`.

### 4. Backend Bundling (Optional for Production)

For true standalone distribution, bundle the Python backend with PyInstaller:

```bash
cd backend
./build.sh
```

This creates a standalone backend executable in `backend/dist/app/`.

**Note**: Backend bundling is optional for development. The Electron app can use the system Python in development mode.

## Distribution

### Windows

**Installer**: `frontend/dist/AntariksClipper-Setup-[version].exe`
- NSIS installer with custom installation directory
- Creates desktop and start menu shortcuts
- Approximately 100-500MB depending on bundling

**Portable**: `frontend/dist/AntariksClipper-[version].exe`
- Runs without installation
- Extracts to a temporary directory

### macOS

**DMG**: `frontend/dist/Antariks Clipper-[version].dmg`
- Disk image for distribution
- Drag-and-drop installation

**ZIP**: `frontend/dist/Antariks Clipper-[version]-mac.zip`
- Direct archive of the app bundle
- Unzip and move to Applications

### Linux

**AppImage**: `frontend/dist/Antariks Clipper-[version].AppImage`
- Self-contained executable
- Works on most Linux distributions
- Make executable: `chmod +x Antariks\ Clipper-[version].AppImage`

**DEB**: `frontend/dist/antariks-clipper_[version]_amd64.deb`
- For Debian/Ubuntu-based distributions
- Install: `sudo dpkg -i antariks-clipper_[version]_amd64.deb`

## Project Structure

```
antariks-clipper/
├── backend/
│   ├── app.py                      # FastAPI application
│   ├── build-backend.spec          # PyInstaller configuration
│   ├── build.sh                    # Backend build script
│   └── ...
├── frontend/
│   ├── electron/
│   │   ├── main.js                 # Electron main process
│   │   ├── preload.js              # Preload script
│   │   └── backend-launcher.js     # Backend process manager
│   ├── build/                      # Application icons
│   ├── resources/                  # Additional resources (FFmpeg)
│   ├── out/                        # Next.js static export (generated)
│   ├── dist/                       # Electron builds (generated)
│   └── package.json                # Includes Electron scripts
└── DESKTOP_BUILD.md                # This file
```

## Configuration

### Environment Variables

**Development** (`frontend/.env.development`):
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Production** (`frontend/.env.production`):
```
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

### Electron Configuration

Main configuration in `frontend/package.json` under the `build` section:

```json
{
  "build": {
    "appId": "com.antariks.clipper",
    "productName": "Antariks Clipper",
    "files": ["out/**/*", "electron/**/*"],
    "extraResources": [
      {
        "from": "../backend",
        "to": "backend",
        "filter": ["**/*", "!.venv/**/*", "!data/**/*"]
      }
    ]
  }
}
```

## Troubleshooting

### Development Issues

#### "Backend failed to start"

**Cause**: Python or dependencies not available

**Solutions**:
1. Verify Python is installed: `python --version` or `python3 --version`
2. Activate virtual environment and install dependencies
3. Check backend logs in the Electron console (DevTools)
4. Try running backend manually: `cd backend && uvicorn app:app --reload`

#### "Cannot find module 'electron'"

**Cause**: Dependencies not installed

**Solution**:
```bash
cd frontend
npm install
```

#### Port 8000 already in use

**Cause**: Another backend instance is running

**Solutions**:
1. Stop other backend processes
2. Change port in `frontend/electron/backend-launcher.js`

### Build Issues

#### "Application icon not found"

**Cause**: Icon files missing in `frontend/build/`

**Solutions**:
1. Add icon files as described in "Prepare Application Icons"
2. Or temporarily comment out icon paths in `package.json` build config

#### Build fails with Python errors

**Cause**: Backend bundling issues

**Solutions**:
1. Skip backend bundling for testing (use system Python)
2. Check PyInstaller installation: `pip install pyinstaller`
3. Review `backend/build-backend.spec` for missing dependencies

#### "out directory not found"

**Cause**: Frontend not built before Electron packaging

**Solution**:
```bash
cd frontend
npm run export
```

### Runtime Issues

#### Application starts but shows blank screen

**Causes**:
- Frontend not properly exported
- Incorrect URL in production

**Solutions**:
1. Check Electron console for errors (enable DevTools)
2. Verify `frontend/out/` exists and contains HTML files
3. Rebuild frontend: `npm run export`

#### Backend API calls fail

**Causes**:
- Backend didn't start properly
- CORS issues
- API URL misconfigured

**Solutions**:
1. Check if backend health endpoint responds: `curl http://127.0.0.1:8000/health`
2. Check backend logs in Electron console
3. Verify `NEXT_PUBLIC_API_URL` in `.env.production`

#### Video processing fails

**Cause**: FFmpeg not found

**Solutions**:
1. Install FFmpeg on the system
2. For Windows distribution, bundle FFmpeg in `frontend/resources/ffmpeg/`
3. Update backend to detect bundled FFmpeg

### Production Distribution Issues

#### Installer is very large (>500MB)

**Causes**:
- Electron runtime is large (~150MB)
- Python dependencies add significant size
- FFmpeg binaries (~100MB)

**Solutions**:
- This is expected for Electron apps
- Consider using installer compression
- Split downloads (app + optional components)

#### Windows Defender blocks installer

**Cause**: Unsigned executable

**Solutions**:
1. Code sign the application (requires certificate)
2. Users can bypass SmartScreen warning
3. Submit to Microsoft for reputation building

#### macOS "App is damaged" error

**Cause**: Unsigned/unnotarized application

**Solutions**:
1. Code sign and notarize the app (requires Apple Developer account)
2. Users can bypass: Right-click > Open
3. Or: `xattr -cr "Antariks Clipper.app"`

## Advanced Configuration

### Auto-Update

To implement auto-updates, integrate `electron-updater`:

1. Install: `npm install electron-updater`
2. Configure update server
3. Add update checking to `main.js`

See: https://www.electron.build/auto-update

### System Tray

Add system tray functionality:

1. Import `Tray` from electron
2. Create tray icon
3. Add menu items (Show/Hide, Quit)

### Custom Splash Screen

Show loading screen while backend starts:

1. Create splash window
2. Show during backend initialization
3. Close when main window is ready

## Resources

- [Electron Documentation](https://www.electronjs.org/docs)
- [Electron Builder](https://www.electron.build/)
- [PyInstaller Manual](https://pyinstaller.org/en/stable/)
- [Next.js Static Export](https://nextjs.org/docs/app/building-your-application/deploying/static-exports)

## License

Same as main project (MIT)
