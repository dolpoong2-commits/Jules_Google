const { contextBridge, ipcRenderer } = require('electron');

// We are exposing a controlled API to the renderer process.
// The renderer can call `window.electronAPI.openFile()` to trigger the main process's file dialog.
contextBridge.exposeInMainWorld('electronAPI', {
  openFile: () => ipcRenderer.invoke('dialog:openFile')
});

console.log('Preload script executed. API exposed.');