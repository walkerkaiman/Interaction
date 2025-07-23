const http = require('http');
const fs = require('fs');
const path = require('path');
const WebSocket = require('ws');
const { spawn } = require('child_process');
// Cross-platform browser opener
function openBrowser(url) {
  const start =
    process.platform === 'darwin'
      ? 'open'
      : process.platform === 'win32'
      ? 'start'
      : 'xdg-open';
  spawn(start, [url], { shell: true, stdio: 'ignore', detached: true });
}

const PORT = 3000;
const LOADING_HTML = path.join(__dirname, 'loading.html');

// Serve loading.html and static assets
const server = http.createServer((req, res) => {
  if (req.url === '/loading.html' || req.url === '/') {
    res.writeHead(200, { 'Content-Type': 'text/html' });
    fs.createReadStream(LOADING_HTML).pipe(res);
  } else {
    res.writeHead(404);
    res.end('Not found');
  }
});

// WebSocket server for logs
const wss = new WebSocket.Server({ server, path: '/logs' });
let sockets = [];
wss.on('connection', (ws) => {
  sockets.push(ws);
  ws.on('close', () => {
    sockets = sockets.filter(s => s !== ws);
  });
});
function broadcast(msg) {
  sockets.forEach(ws => {
    if (ws.readyState === WebSocket.OPEN) ws.send(msg);
  });
}

server.listen(PORT, () => {
  console.log(`Loading screen available at http://localhost:${PORT}/loading.html`);
  openBrowser(`http://localhost:${PORT}/loading.html`);
  startProcesses();
});

// Start backend and frontend processes, stream logs
function startProcesses() {
  // 1. Build and start backend
  const backendDir = path.join(__dirname, 'backend');
  const backendBuild = spawn('npm', ['run', 'build'], { cwd: backendDir, shell: true });
  backendBuild.stdout.on('data', d => broadcast('[backend build] ' + d.toString().trim()));
  backendBuild.stderr.on('data', d => broadcast('[backend build] ' + d.toString().trim()));
  backendBuild.on('close', (code) => {
    if (code !== 0) {
      broadcast('[backend build] exited with code ' + code);
      return;
    }
    broadcast('[backend build] done.');
    // Start backend server
    const backendStart = spawn('npm', ['start'], { cwd: backendDir, shell: true });
    backendStart.stdout.on('data', d => {
      const msg = d.toString().trim();
      broadcast('[backend] ' + msg);
      if (/server started|listening|ready/i.test(msg)) {
        broadcast('__READY__');
      }
    });
    backendStart.stderr.on('data', d => broadcast('[backend] ' + d.toString().trim()));
    backendStart.on('close', code => broadcast('[backend] exited with code ' + code));
  });

  // 2. Build frontend
  const frontendDir = path.join(__dirname, 'web-frontend');
  const frontendBuild = spawn('npm', ['run', 'build'], { cwd: frontendDir, shell: true });
  frontendBuild.stdout.on('data', d => broadcast('[frontend build] ' + d.toString().trim()));
  frontendBuild.stderr.on('data', d => broadcast('[frontend build] ' + d.toString().trim()));
  frontendBuild.on('close', (code) => {
    if (code !== 0) {
      broadcast('[frontend build] exited with code ' + code);
      return;
    }
    broadcast('[frontend build] done.');
    // Optionally, you can start the frontend dev server here if needed
  });
} 