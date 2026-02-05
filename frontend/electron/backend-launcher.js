const { spawn } = require('child_process');
const path = require('path');
const http = require('http');
const isDev = require('electron-is-dev');

class BackendLauncher {
  constructor() {
    this.backendProcess = null;
    this.port = 8000;
    this.maxRetries = 30;
    this.retryDelay = 1000;
  }

  /**
   * Get the Python executable path
   * In development: use system Python
   * In production: use bundled Python/PyInstaller exe
   */
  getPythonPath() {
    if (isDev) {
      // Development: use system Python
      return process.platform === 'win32' ? 'python' : 'python3';
    } else {
      // Production: use bundled backend executable
      const exeName = process.platform === 'win32' ? 'app.exe' : 'app';
      return path.join(process.resourcesPath, 'backend', exeName);
    }
  }

  /**
   * Get the backend working directory
   */
  getBackendDir() {
    if (isDev) {
      // Development: use backend directory relative to project root
      return path.join(__dirname, '..', '..', 'backend');
    } else {
      // Production: use bundled backend directory
      return path.join(process.resourcesPath, 'backend');
    }
  }

  /**
   * Check if backend is responding
   */
  async checkHealth() {
    return new Promise((resolve) => {
      const req = http.get(`http://127.0.0.1:${this.port}/health`, (res) => {
        resolve(res.statusCode === 200);
      });
      
      req.on('error', () => {
        resolve(false);
      });
      
      req.setTimeout(2000, () => {
        req.destroy();
        resolve(false);
      });
    });
  }

  /**
   * Wait for backend to be ready
   */
  async waitForBackend() {
    console.log('Waiting for backend to be ready...');
    
    for (let i = 0; i < this.maxRetries; i++) {
      const isHealthy = await this.checkHealth();
      
      if (isHealthy) {
        console.log('✓ Backend is ready!');
        return true;
      }
      
      console.log(`Waiting for backend... (${i + 1}/${this.maxRetries})`);
      await new Promise(resolve => setTimeout(resolve, this.retryDelay));
    }
    
    console.error('❌ Backend failed to start within timeout');
    return false;
  }

  /**
   * Start the backend process
   */
  async start() {
    console.log('Starting backend...');
    
    const pythonPath = this.getPythonPath();
    const backendDir = this.getBackendDir();
    
    console.log('Python path:', pythonPath);
    console.log('Backend directory:', backendDir);
    
    let args;
    if (isDev) {
      // Development: run with uvicorn
      args = ['-m', 'uvicorn', 'app:app', '--host', '127.0.0.1', '--port', String(this.port)];
    } else {
      // Production: run PyInstaller executable directly
      args = [];
    }
    
    console.log('Starting backend with args:', args);
    
    try {
      this.backendProcess = spawn(pythonPath, args, {
        cwd: backendDir,
        stdio: ['ignore', 'pipe', 'pipe'],
        env: {
          ...process.env,
          PYTHONUNBUFFERED: '1'
        }
      });
      
      this.backendProcess.stdout.on('data', (data) => {
        console.log('[Backend]', data.toString().trim());
      });
      
      this.backendProcess.stderr.on('data', (data) => {
        console.error('[Backend Error]', data.toString().trim());
      });
      
      this.backendProcess.on('exit', (code) => {
        console.log(`Backend process exited with code ${code}`);
        this.backendProcess = null;
      });
      
      this.backendProcess.on('error', (err) => {
        console.error('Failed to start backend:', err);
        this.backendProcess = null;
      });
      
      // Wait for backend to be ready
      const isReady = await this.waitForBackend();
      
      if (!isReady) {
        throw new Error('Backend failed to start');
      }
      
      return true;
    } catch (error) {
      console.error('Error starting backend:', error);
      return false;
    }
  }

  /**
   * Stop the backend process
   */
  stop() {
    if (this.backendProcess) {
      console.log('Stopping backend...');
      
      try {
        if (process.platform === 'win32') {
          // Windows: use taskkill for graceful shutdown
          spawn('taskkill', ['/pid', this.backendProcess.pid, '/f', '/t']);
        } else {
          // Unix: send SIGTERM
          this.backendProcess.kill('SIGTERM');
        }
        
        this.backendProcess = null;
        console.log('✓ Backend stopped');
      } catch (error) {
        console.error('Error stopping backend:', error);
      }
    }
  }
}

module.exports = BackendLauncher;
