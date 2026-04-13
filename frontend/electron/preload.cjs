const { contextBridge, ipcRenderer } = require('electron');

// Expose safe APIs to the renderer process
// Note: Use getBackendConfig() for reliable port discovery in production
// The process.argv parsing is unreliable in preload context
contextBridge.exposeInMainWorld('electronAPI', {
  platform: process.platform,
  skipLoading: () => ipcRenderer.send('skip-loading'),
  getBackendConfig: () => ipcRenderer.invoke('get-backend-config'),
});
