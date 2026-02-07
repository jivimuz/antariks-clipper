const { app, BrowserWindow, dialog, protocol, Menu, shell } = require('electron');
const path = require('path');
const fs = require('fs');
const isDev = !app.isPackaged;
const BackendLauncher = require('./backend-launcher');

let mainWindow = null;
let backendLauncher = null;

// Register custom protocol scheme BEFORE app.ready
if (!isDev) {
  protocol.registerSchemesAsPrivileged([
    {
      scheme: 'app',
      privileges: {
        standard: true,
        secure: true,
        supportFetchAPI: true,
        corsEnabled: true,
        bypassCSP: true,
        stream: true
      }
    }
  ]);
}

/**
 * Create the main application window
 */
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      webSecurity: isDev, // Disable web security in production for custom protocol
    },
    show: false, // Don't show until ready
    title: 'Antariks Clipper'
  });

  // Create application menu
  const menuTemplate = [
    {
      label: 'File',
      submenu: [
        {
          label: 'Home',
          accelerator: 'Ctrl+H',
          click: () => {
            const homeUrl = isDev ? 'http://localhost:3210/' : 'app://./index.html';
            mainWindow.loadURL(homeUrl);
          }
        },
        {
          label: 'Back',
          accelerator: 'Alt+Left',
          click: () => {
            if (mainWindow.webContents.canGoBack()) {
              mainWindow.webContents.goBack();
            }
          }
        },
        {
          label: 'Forward',
          accelerator: 'Alt+Right',
          click: () => {
            if (mainWindow.webContents.canGoForward()) {
              mainWindow.webContents.goForward();
            }
          }
        },
        {
          label: 'Refresh',
          accelerator: 'F5',
          click: () => {
            mainWindow.webContents.reload();
          }
        },
        { type: 'separator' },
        {
          label: 'Exit',
          accelerator: 'Alt+F4',
          click: () => {
            app.quit();
          }
        }
      ]
    },
    {
      label: 'View',
      submenu: [
        // {
        //   label: 'Toggle DevTools',
        //   accelerator: 'F12',
        //   click: () => {
        //     mainWindow.webContents.toggleDevTools();
        //   }
        // },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' }
      ]
    },
    {
      label: 'Help',
      submenu: [
        {
          label: 'Documentation',
          click: async () => {
            await shell.openExternal('https://saas.antariks.id');
          }
        },
        { type: 'separator' },
        {
          label: 'About',
          click: () => {
            dialog.showMessageBox(mainWindow, {
              type: 'info',
              title: 'About Antariks Clipper',
              message: 'Antariks Clipper',
              detail: `Version: ${app.getVersion()}\n\nVideo clipping and rendering application.`
            });
          }
        }
      ]
    }
  ];

  const menu = Menu.buildFromTemplate(menuTemplate);
  Menu.setApplicationMenu(menu);

  // Load the app
  let startUrl;
  if (isDev) {
    // Development: load from Next.js dev server
    startUrl = 'http://localhost:3210';
  } else {
    // Production: load from custom app:// protocol
    startUrl = 'app://./index.html';
  }

  console.log('Loading URL:', startUrl);
  mainWindow.loadURL(startUrl);

  // Show window when ready
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  // Open DevTools in development AND production (for debugging)
  // TODO: Remove this line after fixing issues
  mainWindow.webContents.openDevTools();

  // Prevent navigation to unexpected URLs
  mainWindow.webContents.on('will-navigate', (event, url) => {
    const currentURL = mainWindow.webContents.getURL();
    
    if (!isDev) {
      // Production: allow app:// navigation (same origin)
      if (!url.startsWith('app://')) {
        event.preventDefault();
        console.log('Blocked external navigation to:', url);
      }
      return;
    }

    // Development: only allow localhost navigation
    if (isDev && !url.startsWith('http://localhost:3210')) {
      event.preventDefault();
      console.log('Blocked navigation to:', url);
    }
  });

  // Handle new window requests
  // mainWindow.webContents.setWindowOpenHandler(({ url }) => {
  //   // Block all new windows
  //   console.log('Blocked new window to:', url);
  //   return { action: 'deny' };
  // });

  // Cleanup on close
  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}



/**
 * Create loading splash window
 */
function createSplashWindow() {
  const splash = new BrowserWindow({
    width: 600,
    height: 400,
    frame: false,
    transparent: true,
    alwaysOnTop: true,
    center: true,
    resizable: false,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true
    }
  });

  // Simple loading HTML
  splash.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(`
    <!DOCTYPE html>
    <html>
      <head>
        <style>
          * { margin: 0; padding: 0; box-sizing: border-box; }
          body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100vh;
            color: #fff;
          }
          .container {
            text-align: center;
            padding: 40px;
            background: rgba(15, 23, 42, 0.8);
            border-radius: 20px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
          }
          .logo {
            font-size: 32px;
            font-weight: bold;
            margin-bottom: 20px;
            background: linear-gradient(135deg, #10b981, #14b8a6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
          }
          .spinner {
            border: 3px solid rgba(255, 255, 255, 0.1);
            border-top: 3px solid #10b981;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 20px auto;
          }
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
          .status {
            font-size: 14px;
            color: #94a3b8;
            margin-top: 10px;
          }
        </style>
      </head>
      <body>
        <div class="container">
          <div class="logo">Antariks Clipper</div>
          <div class="spinner"></div>
          <div class="status">Starting server...</div>
        </div>
      </body>
    </html>
  `)}`);

  return splash;
}

/**
 * Initialize the application
 */
async function initialize() {
  console.log('Initializing Antariks Clipper...');
  console.log('Platform:', process.platform);
  console.log('Development mode:', isDev);
  console.log('Resources path:', process.resourcesPath);

  if (!isDev) {
    const outDir = path.join(__dirname, '../out');
    protocol.registerFileProtocol('app', (request, callback) => {
      try {
        const parsedUrl = new URL(request.url);
        const hostPart = parsedUrl.hostname && parsedUrl.hostname !== '.' ? parsedUrl.hostname : '';
        let pathPart = decodeURIComponent(parsedUrl.pathname || '');

        // Normalize leading slashes and "./"
        pathPart = pathPart.replace(/^\/+/, '').replace(/^\.\//, '');

        let relativePath = hostPart ? path.join(hostPart, pathPart) : pathPart;

        if (relativePath === '' || relativePath.endsWith('/')) {
          relativePath = path.join(relativePath, 'index.html');
        } else if (!path.extname(relativePath)) {
          const htmlCandidate = path.join(outDir, `${relativePath}.html`);
          if (fs.existsSync(htmlCandidate)) {
            relativePath = `${relativePath}.html`;
          } else {
            relativePath = path.join(relativePath, 'index.html');
          }
        }

        const resolvedPath = path.join(outDir, relativePath);
        if (!fs.existsSync(resolvedPath)) {
          console.warn('Protocol missing file:', request.url, '->', resolvedPath);
        }
        callback({ path: resolvedPath });
      } catch (error) {
        console.error('Protocol resolve error:', error);
        callback({ path: path.join(outDir, 'index.html') });
      }
    });
  }

  // Show loading splash window
  const splash = createSplashWindow();

  // Start backend FIRST
  backendLauncher = new BackendLauncher();
  
  try {
    const backendStarted = await backendLauncher.start();
    
    if (!backendStarted) {
      console.error('⚠️ Backend failed to start - some features will be unavailable');
      
      // Close splash
      splash.close();
      
      const { response } = await dialog.showMessageBox({
        type: 'warning',
        title: 'Backend Warning',
        message: 'Backend server could not start',
        detail: 'The application will run with limited functionality. Transcription and rendering features may not work.\n\nMake sure Python and all dependencies are installed:\ncd backend\npip install -r requirements_minimal.txt',
        buttons: ['Continue Anyway', 'Quit'],
        defaultId: 0,
      });
      
      if (response === 1) {
        app.quit();
        return;
      }
    } else {
      console.log('✓ Backend started successfully');
    }

    // Backend ready, now create main window
    createWindow();
    
    // Close splash after window is ready
    if (mainWindow) {
      mainWindow.once('ready-to-show', () => {
        setTimeout(() => {
          splash.close();
        }, 500);
      });
    } else {
      splash.close();
    }
    
    // Backend ready
  } catch (error) {
    console.error('Failed to initialize:', error);
    
    await dialog.showMessageBox({
      type: 'error',
      title: 'Initialization Error',
      message: 'Failed to start Antariks Clipper',
      detail: error.message,
    });
    
    app.quit();
  }
}

/**
 * Cleanup before quitting
 */
async function cleanup() {
  console.log('Cleaning up...');
  
  if (backendLauncher) {
    backendLauncher.stop();
  }
}

// App lifecycle events
app.whenReady().then(initialize);

app.on('window-all-closed', () => {
  // On macOS, apps typically stay open until explicitly quit
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  // On macOS, recreate window when dock icon is clicked
  if (BrowserWindow.getAllWindows().length === 0) {
    initialize();
  }
});

app.on('before-quit', (event) => {
  event.preventDefault();
  cleanup().then(() => {
    // Force quit after cleanup
    app.exit(0);
  });
});

// Handle IPC messages
const { ipcMain } = require('electron');

ipcMain.handle('get-version', () => {
  return app.getVersion();
});

ipcMain.handle("download-url", async (_event, { url }) => {
  // window hidden khusus download
  const win = new BrowserWindow({
    show: false,
    webPreferences: { sandbox: false },
  });

  const ses = win.webContents.session;

  // pasang listener sekali untuk window ini
  const onWillDownload = (event, item) => {
    // optional: default save path
    const filename = item.getFilename();
    const savePath = path.join(app.getPath("downloads"), filename);
    item.setSavePath(savePath);

    item.once("done", () => {
      // auto close setelah download selesai/cancel
      try { win.close(); } catch {}
      ses.removeListener("will-download", onWillDownload);
    });
  };

  ses.on("will-download", onWillDownload);

  win.webContents.downloadURL(url);

  return { ok: true };
});

// Handle second instance (single instance lock)
const gotTheLock = app.requestSingleInstanceLock();
if (!gotTheLock) {
  app.quit();
} else {
  app.on('second-instance', () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
    }
  });
}

// Graceful shutdown on uncaught errors
process.on('uncaughtException', (error) => {
  console.error('Uncaught exception:', error);
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled rejection at:', promise, 'reason:', reason);
});
