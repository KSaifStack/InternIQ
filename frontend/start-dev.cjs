const { spawn } = require('child_process');
const path = require('path');
const net = require('net');
const fs = require('fs');

console.log('Starting InternIQ in development mode...\n');

const FRONTEND_PORT = 5173;
const BACKEND_PORT = 8000;

const waitForPort = (port, { host = '127.0.0.1', timeoutMs = 60000 } = {}) =>
  new Promise((resolve, reject) => {
    const start = Date.now();
    const tryConnect = () => {
      const socket = net.createConnection({ port, host });
      socket.once('connect', () => {
        socket.end();
        resolve();
      });
      socket.once('error', () => {
        socket.destroy();
        if (Date.now() - start > timeoutMs) {
          reject(new Error(`Timed out waiting for ${host}:${port}`));
          return;
        }
        setTimeout(tryConnect, 500);
      });
    };
    tryConnect();
  });

// Start Vite frontend
console.log('[1/3] Starting Vite frontend...\n');
const viteProcess = spawn('npm', ['run', 'dev'], {
  cwd: __dirname,
  stdio: 'inherit',
  env: { ...process.env },
  shell: process.platform === 'win32',
});

// Start Python backend
console.log('\n[2/3] Starting Python backend...\n');
const candidatePythonCommands =
  process.platform === 'win32'
    ? [
        path.join('..', 'backend', 'venv', 'Scripts', 'python.exe'), // optional project venv
        'python',
        'py',
      ]
    : [path.join('..', 'backend', 'venv', 'bin', 'python'), 'python3', 'python'];

const uvicornArgs = [
  '-m',
  'uvicorn',
  'backend.main:app',
  '--host',
  '0.0.0.0',
  '--port',
  String(BACKEND_PORT),
  '--reload',
];

const resolveIfFile = (p) => {
  if (p === 'python' || p === 'python3' || p === 'py') return p;
  const abs = path.resolve(__dirname, p);
  try {
    if (!fs.existsSync(abs)) return null;
    const st = fs.statSync(abs);
    return st.isFile() ? abs : null;
  } catch {
    return null;
  }
};

const spawnFirstWorking = (commands, args, options, onError) => {
  let idx = 0;
  const tryNext = () => {
    if (idx >= commands.length) return onError(new Error('No Python executable found'));
    const cmdRaw = commands[idx++];
    const cmd = resolveIfFile(cmdRaw) || cmdRaw; // keep raw for PATH-based commands
    const child = spawn(cmd, args, options);
    child.once('error', (err) => {
      // try next candidate
      tryNext();
    });
    child.once('spawn', () => {
      child.removeAllListeners('error'); // don't retry after successful spawn
      child.on('error', () => {}); // swallow later errors
    });
    return child;
  };
  return tryNext();
};

const pythonProcess = spawnFirstWorking(
  candidatePythonCommands,
  uvicornArgs,
  { cwd: path.join(__dirname, '..'), stdio: 'inherit', shell: process.platform === 'win32' },
  (err) => {
    console.error('\nFailed to start Python backend:', err.message);
    console.error('Fix: install Python (or `py` launcher), or ensure `python` is on your PATH.');
    try {
      viteProcess.kill();
    } catch {}
    process.exit(1);
  }
);

// We no longer wait for ports here. Electron handles waiting via the loading screen!

  console.log('\n[3/3] Starting Electron...\n');
  const electronProcess = spawn('npx', ['electron', 'electron/main.cjs'], {
    cwd: __dirname,
    stdio: 'inherit',
    env: { ...process.env, NODE_ENV: 'development' },
    shell: process.platform === 'win32',
  });

  electronProcess.on('close', (code) => {
    console.log(`\nElectron exited with code ${code}`);
    killAll();
    process.exit(code);
  });

// Kill entire process trees on Windows, plain kill on Unix
function killAll() {
  const isWin = process.platform === 'win32';
  const { execSync } = require('child_process');
  // Kill Vite
  try {
    if (isWin && viteProcess.pid) {
      execSync(`taskkill /pid ${viteProcess.pid} /f /t 2>nul`, { stdio: 'ignore' });
    } else {
      viteProcess.kill();
    }
  } catch {}
  // Kill Python backend
  try {
    if (isWin && pythonProcess.pid) {
      execSync(`taskkill /pid ${pythonProcess.pid} /f /t 2>nul`, { stdio: 'ignore' });
    } else {
      pythonProcess.kill();
    }
  } catch {}
}

// Handle cleanup
process.on('SIGINT', () => {
  console.log('\nShutting down...');
  killAll();
  process.exit(0);
});

process.on('SIGTERM', () => {
  killAll();
  process.exit(0);
});

