const { app, BrowserWindow, dialog } = require('electron');
const path = require('path');
const isDev = require('electron-is-dev');
const BackendLauncher = require('./backend-launcher');

let mainWindow = null;
let backendLauncher = null;

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
    },
    show: false, // Don't show until backend is ready
  });

  // Load the app
  const startUrl = isDev
    ? 'http://localhost:3000'
    : `file://${path.join(__dirname, '../out/index.html')}`;

  console.log('Loading URL:', startUrl);
  mainWindow.loadURL(startUrl);

  // Show window when ready
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  // Open DevTools in development
  if (isDev) {
    mainWindow.webContents.openDevTools();
  }

  // Cleanup on close
  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

/**
 * Initialize the application
 */
async function initialize() {
  console.log('Initializing Antariks Clipper...');
  console.log('Platform:', process.platform);
  console.log('Development mode:', isDev);

  // Start backend
  backendLauncher = new BackendLauncher();
  
  try {
    const backendStarted = await backendLauncher.start();
    
    if (!backendStarted) {
      const { response } = await dialog.showMessageBox({
        type: 'error',
        title: 'Backend Error',
        message: 'Failed to start the backend server',
        detail: 'Please check if Python is installed and all dependencies are available.',
        buttons: ['OK', 'Quit'],
        defaultId: 1,
      });
      
      if (response === 1) {
        app.quit();
        return;
      }
    }
    
    // Create window after backend is ready
    createWindow();
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
    createWindow();
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

// Graceful shutdown on uncaught errors
process.on('uncaughtException', (error) => {
  console.error('Uncaught exception:', error);
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled rejection at:', promise, 'reason:', reason);
});
