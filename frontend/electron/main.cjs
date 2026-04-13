const { app, BrowserWindow, dialog, ipcMain, Menu, shell } = require('electron');
const path = require('path');
const { spawn, execSync } = require('child_process');
const net = require('net');
const http = require('http');
const fs = require('fs');

let mainWindow = null;
let loadingWindow = null;
let pythonProcess = null;
let assignedPort = 8000;

// Check if we're in development
const isDev = process.env.NODE_ENV === 'development' || !app.isPackaged;

// ─────────────────────────────────────────────────────────────────────────────
// Utility helpers
// ─────────────────────────────────────────────────────────────────────────────

const isPortInUse = (port) =>
  new Promise((resolve) => {
    const tester = net
      .createServer()
      .once('error', () => resolve(true))
      .once('listening', () => { tester.close(); resolve(false); })
      .listen(port);
  });

const getOpenPort = () =>
  new Promise((resolve, reject) => {
    const server = net.createServer();
    server.unref();
    server.on('error', reject);
    server.listen(0, '127.0.0.1', () => {
      const port = server.address().port;
      server.close(() => resolve(port));
    });
  });



function httpCheck(url) {
  return new Promise((resolve) => {
    let settled = false;
    const done = (v) => { if (!settled) { settled = true; resolve(v); } };
    const req = http.get(url, (res) => {
      res.resume();
      done(res.statusCode >= 200 && res.statusCode < 300);
    });
    req.on('error', () => done(false));
    req.setTimeout(2000, () => { req.destroy(); done(false); });
  });
}

// Send a message to the loading window (safe — window may already be closed)
function sendToLoading(channel, payload) {
  if (loadingWindow && !loadingWindow.isDestroyed()) {
    loadingWindow.webContents.send(channel, payload);
  }
}

function killAllChildProcesses() {
  if (process.platform !== 'win32') return;
  try { execSync('taskkill /f /im python.exe /t 2>nul', { stdio: 'ignore' }); } catch {}
  for (const port of [5173, assignedPort]) {
    try {
      const result = execSync(`netstat -ano | findstr :${port} | findstr LISTENING`, { encoding: 'utf8' });
      for (const line of result.trim().split('\n')) {
        const pid = line.trim().split(/\s+/).pop();
        if (pid && pid !== '0') {
          try { execSync(`taskkill /f /pid ${pid} /t 2>nul`, { stdio: 'ignore' }); } catch {}
        }
      }
    } catch {}
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Window factories
// ─────────────────────────────────────────────────────────────────────────────

function createLoadingWindow() {
  loadingWindow = new BrowserWindow({
    width: 480,
    height: 380,
    frame: false,
    transparent: false,
    alwaysOnTop: true,
    resizable: false,
    movable: true,
    show: false,
    backgroundColor: '#f9f7f2',
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'loading-preload.cjs'),
      devTools: false,
    },
  });

  loadingWindow.loadFile(path.join(__dirname, 'loading.html'));
  loadingWindow.once('ready-to-show', () => {
    loadingWindow.center();
    loadingWindow.show();
  });
  loadingWindow.on('closed', () => { loadingWindow = null; });
}

function createMainWindow() {
  if (!isDev) Menu.setApplicationMenu(null);

  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1000,
    minHeight: 700,
    show: false, // Hidden until data is ready
    titleBarStyle: 'default',
    title: 'InternIQ',
    backgroundColor: '#f9f7f2',
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.cjs'),
      webSecurity: true,
      allowRunningInsecureContent: false,
      devTools: isDev,
      additionalArguments: [`--backend-port=${assignedPort}`],
    },
  });

  mainWindow.on('closed', () => { mainWindow = null; });

  // Open external links in system browser
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  // Block DevTools + F5 in production
  if (!isDev) {
    mainWindow.webContents.on('before-input-event', (event, input) => {
      if (
        input.key === 'F12' ||
        (input.control && input.shift && ['I', 'J', 'C'].includes(input.key)) ||
        (input.control && input.key === 'R') ||
        input.key === 'F5'
      ) event.preventDefault();
    });
    mainWindow.webContents.on('context-menu', (e) => e.preventDefault());
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Loading orchestration — polls until data ready, then swaps windows
// ─────────────────────────────────────────────────────────────────────────────

async function waitForMinimumJobs(minimum, timeoutMs = 180000) {
  return new Promise((resolve) => {
    const start = Date.now();
    let lastCount = -1;

    const check = () => {
      if (Date.now() - start > timeoutMs) {
        console.log('[Electron] Job wait timed out — showing app anyway');
        resolve(0);
        return;
      }

      http.get(`http://localhost:${assignedPort}/api/admin/health`, (res) => {
        let body = '';
        res.on('data', (d) => body += d);
        res.on('end', () => {
          try {
            const data = JSON.parse(body);
            const count = data.database?.active_jobs || 0;

            if (count !== lastCount) {
              lastCount = count;
              const pct = Math.min(50 + Math.round((count / minimum) * 45), 95);
              sendToLoading('loading-status', `Syncing 2026 internships… ${count} loaded`);
              sendToLoading('loading-progress', pct);
              console.log(`[Electron] Jobs loaded: ${count}/${minimum}`);
            }

            if (count >= minimum) {
              sendToLoading('loading-status', `✓ ${count} internships ready`);
              sendToLoading('loading-progress', 100);
              resolve(count);
            } else {
              setTimeout(check, 1000);
            }
          } catch {
            setTimeout(check, 1000);
          }
        });
      }).on('error', () => setTimeout(check, 1000));
    };

    check();
  });
}

async function runStartupSequence() {
  // ── Phase 1: Show loading window ──────────────────────────────────────────
  createLoadingWindow();
  sendToLoading('loading-status', 'Starting backend…');
  sendToLoading('loading-progress', 5);

  // ── Phase 2: Create main window (hidden) and start loading Vite/prod ─────
  createMainWindow();

  if (isDev) {
    // In dev: wait for Vite dev server
    let viteReady = false;
    let backendReady = false;
    let pollCount = 0;

    sendToLoading('loading-status', 'Waiting for services…');

    await new Promise((resolve) => {
      const poll = async () => {
        pollCount++;

        if (!viteReady) {
          viteReady = await httpCheck('http://localhost:5173/') ||
                       await httpCheck('http://127.0.0.1:5173/');
          if (viteReady) {
            console.log('[Electron] ✓ Vite ready');
            sendToLoading('loading-status', 'Frontend ready, loading backend…');
            sendToLoading('loading-progress', 20);
          }
        }

        if (!backendReady) {
          backendReady = await httpCheck(`http://127.0.0.1:${assignedPort}/health`);
          if (backendReady) {
            console.log('[Electron] ✓ Backend ready');
            sendToLoading('loading-status', 'Backend ready, syncing jobs…');
            sendToLoading('loading-progress', 35);
          }
        }

        if (pollCount % 10 === 0) {
          console.log(`[Electron] Waiting… vite=${viteReady} backend=${backendReady}`);
        }

        if (viteReady && backendReady) {
          resolve();
        } else {
          setTimeout(poll, 800);
        }
      };
      poll();
    });

    // Load Vite into the (still hidden) main window
    mainWindow.loadURL('http://localhost:5173');
  } else {
    // In production: wait for backend file signal
    sendToLoading('loading-status', 'Starting backend…');
    sendToLoading('loading-progress', 15);

    await new Promise((resolve) => {
      const check = async () => {
        if (await httpCheck(`http://127.0.0.1:${assignedPort}/health`)) { resolve(); }
        else { setTimeout(check, 500); }
      };
      check();
    });

    sendToLoading('loading-status', 'Backend ready, syncing jobs…');
    sendToLoading('loading-progress', 35);
    mainWindow.loadFile(path.join(__dirname, '..', 'dist', 'index.html'));
  }

  // ── Phase 3: Wait for job data ────────────────────────────────────────────
  await waitForMinimumJobs(50);

  // ── Phase 4: Show main window, close loading window ───────────────────────
  await new Promise((resolve) => {
    // Give React a moment to mount after navigation
    const show = () => {
      if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.show();
        mainWindow.focus();
      }
      if (loadingWindow && !loadingWindow.isDestroyed()) {
        // Small delay so the crossfade feels intentional
        setTimeout(() => {
          if (loadingWindow && !loadingWindow.isDestroyed()) loadingWindow.close();
          resolve();
        }, 350);
      } else {
        resolve();
      }
    };

    if (mainWindow.webContents.isLoading()) {
      mainWindow.webContents.once('did-finish-load', show);
    } else {
      show();
    }
  });

  console.log('[Electron] ✓ App ready — loading window closed');
}

// ─────────────────────────────────────────────────────────────────────────────
// Python backend management (production only)
// ─────────────────────────────────────────────────────────────────────────────

async function startPythonBackend() {
  if (isDev) {
    console.log('[Electron] Dev mode: backend started separately');
    assignedPort = 8000;
    return;
  }

  try {
    assignedPort = await getOpenPort();
  } catch {
    assignedPort = 8000;
  }

  const resourcesPath = process.resourcesPath;
  const exeName = process.platform === 'win32' ? 'interniq-backend.exe' : 'interniq-backend';
  const backendExe = path.join(resourcesPath, 'backend', exeName);

  console.log(`[InternIQ] Starting bundled backend on port ${assignedPort}:`, backendExe);

  pythonProcess = spawn(backendExe, [], {
    cwd: path.join(resourcesPath, 'backend'),
    env: { ...process.env, PYTHONUNBUFFERED: '1', APP_ENV: 'production', PORT: assignedPort.toString() },
    stdio: ['ignore', 'pipe', 'pipe'],
  });

  pythonProcess.stdout.on('data', (d) => console.log(`[Python] ${d.toString().trim()}`));
  pythonProcess.stderr.on('data', (d) => console.error(`[Python Error] ${d.toString().trim()}`));
  pythonProcess.on('close', (code) => {
    console.log(`[Python] exited with code ${code}`);
    if (code !== 0) {
      dialog.showErrorBox('Backend Error', `The Python backend crashed (code ${code}).`);
    }
  });
  pythonProcess.on('error', (err) => {
    dialog.showErrorBox('Backend Error', `Failed to start Python backend:\n${err.message}`);
  });
}

function stopPythonBackend() {
  if (pythonProcess) {
    if (process.platform === 'win32') {
      spawn('taskkill', ['/pid', pythonProcess.pid, '/f', '/t']);
    } else {
      pythonProcess.kill('SIGTERM');
    }
    pythonProcess = null;
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// App lifecycle
// ─────────────────────────────────────────────────────────────────────────────

app.whenReady().then(async () => {
  // IPC: renderer asks for backend port
  ipcMain.handle('get-backend-config', () => ({ port: assignedPort }));

  // Production: start bundled backend before showing anything
  if (!isDev) await startPythonBackend();

  // Apply CSP to all sessions
  const { session } = require('electron');
  session.defaultSession.webRequest.onHeadersReceived((details, callback) => {
    callback({
      responseHeaders: {
        ...details.responseHeaders,
        'Content-Security-Policy': [
          "default-src 'self' http://localhost:* http://127.0.0.1:*; " +
          "script-src 'self' 'unsafe-inline'; " +
          "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; " +
          "font-src 'self' https://fonts.gstatic.com; " +
          "img-src 'self' data: https:;"
        ],
      },
    });
  });

  await runStartupSequence();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) runStartupSequence();
});

app.on('before-quit', () => {
  stopPythonBackend();
  killAllChildProcesses();
});

// Security: prevent new window creation
app.on('web-contents-created', (_event, contents) => {
  contents.on('new-window', (event, navigationUrl) => {
    event.preventDefault();
    shell.openExternal(navigationUrl);
  });
});
