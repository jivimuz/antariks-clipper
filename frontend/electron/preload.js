/**
 * Preload script for Electron
 * Runs in a context that has access to both Node.js and DOM APIs
 * Used to securely expose Node.js functionality to the renderer process
 */

const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electron', {
  // Example: send messages to main process
  send: (channel, data) => {
    // Whitelist channels
    const validChannels = ['toMain'];
    if (validChannels.includes(channel)) {
      ipcRenderer.send(channel, data);
    }
  },
  download: (url) => ipcRenderer.invoke("download-url", { url }),
  // Example: receive messages from main process
  receive: (channel, func) => {
    const validChannels = ['fromMain'];
    if (validChannels.includes(channel)) {
      // Deliberately strip event as it includes `sender`
      ipcRenderer.on(channel, (event, ...args) => func(...args));
    }
  },
  
  // Get app version
  getVersion: () => ipcRenderer.invoke('get-version'),
  
  // Platform info
  platform: process.platform
});

console.log('Preload script loaded');
