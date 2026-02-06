# Electron Application Files

This directory contains the Electron main process and related files for the desktop application.

## File Structure

```
electron/
├── main.js              # Electron main process entry point
├── preload.js           # Preload script for secure IPC
└── backend-launcher.js  # Backend process manager
```

## Architecture Overview

### main.js

The main process is the entry point of the Electron application. It:

1. **Initializes the application**
   - Creates the browser window
   - Sets up window properties and web preferences
   - Handles application lifecycle events

2. **Manages servers**
   - Starts the Python backend via `backend-launcher.js`
   - Starts the Next.js production server (in production mode)
   - Ensures servers are running before showing the window

3. **Handles cleanup**
   - Stops backend when app quits
   - Stops Next.js server when app quits
   - Ensures no lingering processes

### backend-launcher.js

Manages the Python FastAPI backend process:

1. **Development mode**
   - Detects system Python
   - Runs `uvicorn app:app --host 127.0.0.1 --port 8000`
   - Uses backend directory relative to project

2. **Production mode**
   - Uses bundled PyInstaller executable
   - Runs from resources directory
   - Self-contained backend

3. **Health checking**
   - Polls `/health` endpoint
   - Waits up to 30 seconds for backend to be ready
   - Reports errors if backend fails to start

4. **Process management**
   - Captures stdout/stderr for logging
   - Handles graceful shutdown
   - Platform-specific termination (SIGTERM on Unix, taskkill on Windows)

### preload.js

Provides secure communication between renderer and main process:

1. **Context isolation**
   - Runs in isolated context with access to both Node.js and DOM
   - Exposes limited, safe APIs to renderer process

2. **IPC bridge**
   - Currently minimal (version info)
   - Can be extended for app-specific IPC needs

3. **Security**
   - Prevents direct Node.js access from renderer
   - Whitelists allowed IPC channels

## Key Concepts

### Development vs Production

**Development Mode** (`isDev = true`):

- Uses system Python and Node.js
- Assumes Next.js dev server running externally
- Hot-reload enabled
- DevTools open by default

**Production Mode** (`isDev = false`):

- Uses bundled backend and frontend
- Starts Next.js production server internally
- Optimized builds
- No DevTools

### Server Lifecycle

1. **Startup sequence**:

   ```
   App Ready → Backend Start → Backend Health Check →
   Next.js Start (prod) → Create Window → Load URL
   ```

2. **Shutdown sequence**:
   ```
   Window Close → Cleanup → Stop Backend →
   Stop Next.js (prod) → App Quit
   ```

### Port Configuration

- **Backend**: Port 3211 (configurable in `backend-launcher.js`)
- **Frontend**: Port 3210 (hardcoded in `main.js`)

To change ports:

1. Update `backend-launcher.js` for backend port
2. Update `main.js` for Next.js port
3. Update `.env.production` for API URL

## Extending the Application

### Adding IPC Communication

To add new IPC channels:

1. **In preload.js**, add to whitelist:

```javascript
contextBridge.exposeInMainWorld("electron", {
  myFunction: (data) => ipcRenderer.invoke("my-channel", data),
});
```

2. **In main.js**, handle the channel:

```javascript
ipcMain.handle("my-channel", async (event, data) => {
  // Handle the request
  return result;
});
```

3. **In renderer**, use the exposed API:

```javascript
const result = await window.electron.myFunction(data);
```

### Adding System Tray

1. Import `Tray` in `main.js`
2. Create tray icon in `initialize()`:

```javascript
const { Tray, Menu } = require("electron");
let tray = new Tray("path/to/icon.png");
const contextMenu = Menu.buildFromTemplate([
  { label: "Show App", click: () => mainWindow.show() },
  { label: "Quit", click: () => app.quit() },
]);
tray.setContextMenu(contextMenu);
```

### Adding Auto-Update

1. Install `electron-updater`:

```bash
npm install electron-updater
```

2. Configure in `main.js`:

```javascript
const { autoUpdater } = require("electron-updater");
autoUpdater.checkForUpdatesAndNotify();
```

3. Add update configuration to `package.json`:

```json
"publish": {
  "provider": "github",
  "owner": "your-username",
  "repo": "antariks-clipper"
}
```

## Debugging

### Main Process

Log statements in main.js and backend-launcher.js appear in the terminal.

### Renderer Process

Open DevTools (View → Toggle Developer Tools) to see console logs.

### Backend Process

Backend logs are captured and logged to console with `[Backend]` prefix.

### Common Issues

1. **Backend won't start**
   - Check Python is available: `python3 --version`
   - Check backend directory path
   - Check port 8000 is not in use

2. **Next.js won't start**
   - Check `.next` directory exists (run `npm run build`)
   - Check port 3000 is not in use
   - Check Node.js is available

3. **Window shows blank screen**
   - Check browser console for errors
   - Verify URLs are correct
   - Check servers are actually running

## Testing

### Manual Testing

```bash
# Test backend launcher
cd backend
source .venv/bin/activate
python3 -m uvicorn app:app --port 8000

# Test health check
curl http://localhost:8000/health

# Test Electron
cd ../frontend
npm run electron
```

### Automated Testing

Currently manual testing only. Future: Add integration tests with Spectron or Playwright.

## Resources

- [Electron Documentation](https://www.electronjs.org/docs)
- [Electron Security Best Practices](https://www.electronjs.org/docs/tutorial/security)
- [IPC Communication](https://www.electronjs.org/docs/latest/tutorial/ipc)
- [Process Model](https://www.electronjs.org/docs/latest/tutorial/process-model)
