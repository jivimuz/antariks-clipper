# Quick Start Guide - Desktop Development

This guide will get you up and running with Antariks Clipper desktop app in development mode.

## Prerequisites Check

Run the validation script to verify your setup:
```bash
./validate-desktop-setup.sh
```

If any checks fail, see the main README.md for setup instructions.

## Development Mode

### 1. Start in Development Mode

The easiest way to develop is to use the `electron-dev` command which starts everything:

```bash
cd frontend
npm run electron-dev
```

This will:
1. ✅ Start Next.js dev server (http://localhost:3000)
2. ✅ Wait for Next.js to be ready
3. ✅ Launch Electron window
4. ✅ Auto-start Python backend (http://localhost:8000)
5. ✅ Open DevTools for debugging

### 2. Manual Mode (Alternative)

If you prefer to run components separately:

**Terminal 1 - Backend:**
```bash
cd backend
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
uvicorn app:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

**Terminal 3 - Electron:**
```bash
cd frontend
npm run electron
```

### 3. Making Changes

- **Frontend changes**: Next.js hot-reload works automatically
- **Backend changes**: The backend runs with `--reload` flag, so it auto-restarts
- **Electron main process changes**: Close and restart `npm run electron-dev`

## Common Development Tasks

### Testing Backend API

```bash
# Health check
curl http://localhost:8000/health

# Test endpoints (with backend running)
curl http://localhost:8000/api/jobs
```

### Viewing Logs

- **Frontend logs**: Browser DevTools Console (opened automatically in dev mode)
- **Backend logs**: Visible in Electron DevTools Console
- **Electron main process logs**: Terminal where you ran `npm run electron-dev`

### Stopping the App

Simply close the Electron window. The backend will automatically stop.

## Building for Production

### Quick Build

```bash
cd frontend
npm run build  # Build Next.js
npm run pack   # Package without creating installer
```

The packaged app will be in `frontend/dist/[platform]-unpacked/`

### Create Installer

```bash
cd frontend
npm run dist       # Build for current platform
# or
npm run dist:win   # Windows
npm run dist:mac   # macOS  
npm run dist:linux # Linux
```

Installers will be in `frontend/dist/`

## Troubleshooting

### Port Already in Use

If port 8000 or 3000 is already in use:

```bash
# Find and kill process on port 8000 (backend)
# Linux/macOS:
lsof -ti:8000 | xargs kill -9
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Find and kill process on port 3000 (frontend)
# Linux/macOS:
lsof -ti:3000 | xargs kill -9
# Windows:
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

### Backend Fails to Start

1. Check Python is activated:
   ```bash
   cd backend
   source .venv/bin/activate
   python --version  # Should show Python 3.8+
   ```

2. Check dependencies:
   ```bash
   pip install -r requirements_minimal.txt
   pip install requests numpy opencv-python boto3 faster-whisper
   ```

3. Test backend manually:
   ```bash
   cd backend
   source .venv/bin/activate
   python -m uvicorn app:app --reload
   ```

### Electron Won't Start

1. Reinstall dependencies:
   ```bash
   cd frontend
   rm -rf node_modules package-lock.json
   npm install
   ```

2. Check Electron is installed:
   ```bash
   cd frontend
   npx electron --version
   ```

### Build Fails

1. Clean build artifacts:
   ```bash
   cd frontend
   rm -rf .next dist node_modules
   npm install
   npm run build
   ```

2. Check for disk space - builds can be large (1-2GB)

## Resources

- [DESKTOP_BUILD.md](../DESKTOP_BUILD.md) - Comprehensive build guide
- [README.md](../README.md) - Main project documentation
- [Electron Documentation](https://www.electronjs.org/docs)
- [Next.js Documentation](https://nextjs.org/docs)

## Need Help?

1. Check the main [README.md](../README.md) troubleshooting section
2. Review [DESKTOP_BUILD.md](../DESKTOP_BUILD.md) for detailed guidance
3. Check logs in DevTools Console
4. Open an issue on GitHub with:
   - Your OS and versions (Node, Python, etc.)
   - Complete error messages
   - Steps to reproduce
