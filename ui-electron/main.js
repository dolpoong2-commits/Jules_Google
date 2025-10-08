const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');

function createWindow() {
  const mainWindow = new BrowserWindow({
    width: 1280,
    height: 720,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true, // It's recommended to keep this true for security
      nodeIntegration: false, // It's recommended to keep this false for security
    },
  });

  // Load the index.html of the app.
  mainWindow.loadFile('index.html');

  // Open the DevTools for debugging.
  mainWindow.webContents.openDevTools();
}

async function handleFileOpen() {
  const { canceled, filePaths } = await dialog.showOpenDialog({
    properties: ['openFile'],
    filters: [
      { name: 'SolidWorks Files', extensions: ['SLDASM', 'SLDPRT'] }
    ]
  });
  if (!canceled) {
    return filePaths[0];
  }
}

app.whenReady().then(() => {
  ipcMain.handle('dialog:openFile', handleFileOpen);
  createWindow();

  app.on('activate', function () {
    // On macOS it's common to re-create a window in the app when the
    // dock icon is clicked and there are no other windows open.
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', function () {
  // Quit when all windows are closed, except on macOS.
  if (process.platform !== 'darwin') app.quit();
});