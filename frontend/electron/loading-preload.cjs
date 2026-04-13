/**
 * Preload script for the frameless loading window.
 * Exposes only one IPC channel: receiving status text updates from main.
 */
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('loadingAPI', {
  onStatus: (callback) => ipcRenderer.on('loading-status', (_event, msg) => callback(msg)),
  onProgress: (callback) => ipcRenderer.on('loading-progress', (_event, pct) => callback(pct)),
});
