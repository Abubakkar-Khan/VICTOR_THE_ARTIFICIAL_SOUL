const { app, BrowserWindow, screen } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let workshopWindow = null;
let companionWindow = null;
let pythonProcess = null;

function startBackend() {
  const pythonCmd = process.platform === 'win32' ? 'python' : 'python3';
  pythonProcess = spawn(pythonCmd, ['-m', 'dexter.api.server'], {
    cwd: path.join(__dirname, '..'),
    shell: true,
    stdio: 'ignore'
  });
}

function createWorkshopWindow() {
  workshopWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 960,
    minHeight: 640,
    backgroundColor: '#11110F',
    title: 'Dexter — The Artificial Soul',
    icon: path.join(__dirname, '../dexter/sprite/icon.ico'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true
    }
  });

  workshopWindow.loadURL('http://127.0.0.1:8000');

  workshopWindow.on('closed', () => {
    workshopWindow = null;
  });
}

function createCompanionWindow() {
  const primaryDisplay = screen.getPrimaryDisplay();
  const { width: screenWidth, height: screenHeight } = primaryDisplay.workAreaSize;

  companionWindow = new BrowserWindow({
    width: 240,
    height: 250,
    x: screenWidth - 260,
    y: screenHeight - 270,
    frame: false,
    transparent: true,
    alwaysOnTop: true,
    resizable: false,
    skipTaskbar: true,
    hasShadow: false,
    icon: path.join(__dirname, '../dexter/sprite/icon.ico'),
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  });

  companionWindow.loadFile(path.join(__dirname, 'companion.html'));

  companionWindow.on('closed', () => {
    companionWindow = null;
  });
}

app.whenReady().then(() => {
  startBackend();
  // Brief delay to allow FastAPI server initialization
  setTimeout(() => {
    createCompanionWindow();
    createWorkshopWindow();
  }, 1500);
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('will-quit', () => {
  if (pythonProcess) {
    try {
      pythonProcess.kill();
    } catch (e) {}
  }
});
