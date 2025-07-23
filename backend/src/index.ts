import express, { Request, Response } from 'express';
import path from 'path';
import http from 'http';
import { WebSocketServer, WebSocket } from 'ws';
import fs from 'fs';

import { Logger } from './core/Logger';
import { ModuleLoader } from './core/ModuleLoader';
import multer from 'multer';
import { MessageRouter } from './core/MessageRouter';
import { getSystemStats, getSystemInfo, getProcesses, getServices } from './core/SystemStats';

const app = express();
app.use(express.json());

// Add CORS headers for loading screen
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept');
  if (req.method === 'OPTIONS') {
    res.sendStatus(200);
  } else {
    next();
  }
});

const logger = new Logger('System');
const moduleLoader = new ModuleLoader(logger);

console.log('=== Backend server starting, using', __filename);
console.log('=== TEST LOG: index.ts loaded ===');

// Catch-all API log (before all API endpoints)
app.use('/api', (req, res, next) => {
  console.log('DEBUG: API request received:', req.method, req.originalUrl);
  next();
});

// --- Load config and instantiate modules ---
const configPath = path.join(__dirname, '../../config/interactions/interactions.json');
let interactions: any[] = [];
let modules: any[] = [];
try {
  const config = JSON.parse(fs.readFileSync(configPath, 'utf-8'));
  interactions = config.interactions || [];
  modules = moduleLoader.loadModulesFromConfig(configPath);
  logger.log(`Loaded ${modules.length} modules from config`, 'System');
} catch (e) {
  logger.log('Failed to load config: ' + e, 'Error');
}

let messageRouter = new MessageRouter(interactions, modules);

// --- WebSocket setup ---
const server = http.createServer(app);
const wss = new WebSocketServer({ server });
function broadcastWS(data: any) {
  const msg = JSON.stringify(data);
  wss.clients.forEach((client: WebSocket) => {
    if (client.readyState === 1) client.send(msg);
  });
}
logger.setBroadcast(broadcastWS);
wss.on('connection', (ws: WebSocket) => {
  // On connect, send current state of all modules
  ws.send(JSON.stringify({ type: 'all_modules', modules: modules.map(m => ({ id: m.getModuleName(), config: m.config })) }));
});

// Periodically broadcast system stats
setInterval(async () => {
  try {
    const stats = await getSystemStats();
    logger.log(`CPU: ${(stats.cpu * 100).toFixed(1)}%, Mem: ${(stats.memory * 100).toFixed(1)}%`, 'Performance');
    broadcastWS({ type: 'system_stats', ...stats });
  } catch (err) {
    logger.log('Error broadcasting system stats: ' + err, 'Error');
  }
}, 1000);

// --- API Endpoints ---
app.get('/api/status', (req, res) => {
  res.json({ 
    status: 'ready', 
    timestamp: new Date().toISOString(),
    modules: modules.length,
    interactions: interactions.length
  });
});

app.get('/api/system_info', async (req, res) => {
  try {
    const info = await getSystemInfo();
    res.json(info);
  } catch (err) {
    logger.log('Failed to get system info: ' + err, 'Error');
    res.status(500).json({ error: 'Failed to get system info' });
  }
});

app.get('/api/processes', async (req, res) => {
  try {
    const procs = await getProcesses();
    res.json(procs);
  } catch (err) {
    logger.log('Failed to get processes: ' + err, 'Error');
    res.status(500).json({ error: 'Failed to get processes' });
  }
});

app.get('/api/services', async (req, res) => {
  try {
    const names = req.query.names as string | undefined;
    const services = await getServices(names);
    res.json(services);
  } catch (err) {
    logger.log('Failed to get services: ' + err, 'Error');
    res.status(500).json({ error: 'Failed to get services' });
  }
});

app.get('/api/module_wikis', (req: Request, res: Response) => {
  const wikiDir = path.join(__dirname, '../../web-frontend/module_wikis');
  fs.readdir(wikiDir, (err, files) => {
    if (err) return res.status(500).json({ error: 'Failed to read wiki directory' });
    const mdFiles = files.filter(f => f.endsWith('.md'));
    res.json(mdFiles);
  });
});

app.get('/api/module_wiki/:module', (req: Request, res: Response) => {
  const moduleName = req.params.module;
  // Correct path: backend/src/modules/<module>/wiki.md
  const wikiPath = path.resolve(__dirname, '../src/modules', moduleName, 'wiki.md');
  console.log('Serving wiki:', wikiPath, fs.existsSync(wikiPath));
  if (!fs.existsSync(wikiPath)) {
    return res.status(404).send('Wiki not found');
  }
  res.sendFile(wikiPath);
});

app.get('/modules', (req: Request, res: Response) => {
  res.json(moduleLoader.getAvailableModules());
});

// --- Settings update endpoint ---
app.post('/modules/:id/settings', async (req: Request, res: Response) => {
  const { id } = req.params;
  const newSettings = req.body;
  const mod = modules.find(m => m.getModuleName() === id);
  if (!mod) return res.status(404).json({ error: 'Module not found' });
  mod.lock();
  broadcastWS({ type: 'module_lock', moduleId: id });
  // Update settings in memory
  Object.assign(mod.config, newSettings);
  // Persist to config/interactions/interactions.json
  try {
    const configPath = path.join(__dirname, '../../config/interactions/interactions.json');
    const configData = JSON.parse(fs.readFileSync(configPath, 'utf-8'));
    for (const interaction of configData.interactions) {
      if (interaction.input && interaction.input.module === id) {
        Object.assign(interaction.input.config, newSettings);
      }
      if (interaction.output && interaction.output.module === id) {
        Object.assign(interaction.output.config, newSettings);
      }
    }
    fs.writeFileSync(configPath, JSON.stringify(configData, null, 2));
  } catch (err) {
    console.error('Failed to persist module settings:', err);
  }
  // Broadcast update
  broadcastWS({ type: 'module_update', moduleId: id, newState: mod.config });
  mod.unlock();
  broadcastWS({ type: 'module_unlock', moduleId: id });
  res.json({ success: true, newState: mod.config });
});

// --- Mode toggle endpoint ---
app.post('/modules/:id/mode', async (req: Request, res: Response) => {
  const { id } = req.params;
  const { mode } = req.body;
  const mod = modules.find(m => m.getModuleName() === id);
  if (!mod || !mod.setMode) return res.status(404).json({ error: 'Module not found or cannot set mode' });
  mod.lock();
  broadcastWS({ type: 'module_lock', moduleId: id });
  mod.setMode(mode);
  // Persist mode to config/interactions/interactions.json
  try {
    const configPath = path.join(__dirname, '../../config/interactions/interactions.json');
    const configData = JSON.parse(fs.readFileSync(configPath, 'utf-8'));
    for (const interaction of configData.interactions) {
      if (interaction.input && interaction.input.module === id) {
        interaction.input.config.mode = mode;
      }
      if (interaction.output && interaction.output.module === id) {
        interaction.output.config.mode = mode;
      }
    }
    fs.writeFileSync(configPath, JSON.stringify(configData, null, 2));
  } catch (err) {
    console.error('Failed to persist module mode:', err);
  }
  broadcastWS({ type: 'module_mode', moduleId: id, mode });
  mod.unlock();
  broadcastWS({ type: 'module_unlock', moduleId: id });
  res.json({ success: true, mode });
});

// --- Serve waveform PNG for audio_output ---
app.get('/api/module_waveform/:module', (req: Request, res: Response) => {
  const moduleName = req.params.module;
  if (moduleName !== 'audio_output') return res.status(404).send('Not found');
  const mod = modules.find(m => m.getModuleName() === 'audio_output');
  if (!mod || !mod.config.file_path) return res.status(404).send('No audio file');
  const filePath = mod.config.file_path;
  const cacheDir = path.resolve(__dirname, '../src/modules/audio_output/waveform_cache');
  const waveformFile = path.join(cacheDir, path.basename(filePath) + '.waveform.png');
  if (!fs.existsSync(waveformFile)) {
    return res.status(404).send('Waveform not found');
  }
  res.sendFile(waveformFile);
});

// Register a new interaction at runtime
app.post('/api/interactions', async (req: Request, res: Response) => {
  const newInteraction = req.body;
  try {
    const configPath = path.join(__dirname, '../../config/interactions/interactions.json');
    const configData = JSON.parse(fs.readFileSync(configPath, 'utf-8'));
    configData.interactions.push(newInteraction);
    fs.writeFileSync(configPath, JSON.stringify(configData, null, 2));
    // Instantiate new modules for the interaction
    const inputModName = newInteraction.input.module;
    const inputConfig = newInteraction.input.config;
    const outputModName = newInteraction.output.module;
    const outputConfig = newInteraction.output.config;
    const InputClass = moduleLoader.getModuleClass(inputModName);
    const OutputClass = moduleLoader.getModuleClass(outputModName);
    let newInput, newOutput;
    if (InputClass) {
      newInput = new InputClass(inputConfig, logger.log.bind(logger));
      modules.push(newInput);
    }
    if (OutputClass) {
      newOutput = new OutputClass(outputConfig, logger.log.bind(logger));
      modules.push(newOutput);
    }
    // Add to message router
    messageRouter.addInteraction(newInteraction, modules);
    // Broadcast new state to all UIs
    broadcastWS({ type: 'all_modules', modules: modules.map(m => ({ id: m.getModuleName(), config: m.config })) });
    res.json({ success: true, interaction: newInteraction });
  } catch (err) {
    console.error('Failed to register new interaction:', err);
    res.status(500).json({ error: 'Failed to register new interaction' });
  }
});

// (Optional) Add endpoints for removing and updating interactions
app.post('/api/interactions/remove', async (req: Request, res: Response) => {
  const interactionToRemove = req.body;
  try {
    const configPath = path.join(__dirname, '../../config/interactions/interactions.json');
    const configData = JSON.parse(fs.readFileSync(configPath, 'utf-8'));
    configData.interactions = configData.interactions.filter((interaction: any) =>
      !(interaction.input.module === interactionToRemove.input.module &&
        interaction.output.module === interactionToRemove.output.module)
    );
    fs.writeFileSync(configPath, JSON.stringify(configData, null, 2));
    // Remove from message router
    messageRouter.removeInteraction(interactionToRemove);
    // Stop and remove module instances
    const inputIdx = modules.findIndex(m => m.getModuleName() === interactionToRemove.input.module);
    if (inputIdx !== -1) {
      if (typeof modules[inputIdx].stop === 'function') modules[inputIdx].stop();
      modules.splice(inputIdx, 1);
    }
    const outputIdx = modules.findIndex(m => m.getModuleName() === interactionToRemove.output.module);
    if (outputIdx !== -1) {
      if (typeof modules[outputIdx].stop === 'function') modules[outputIdx].stop();
      modules.splice(outputIdx, 1);
    }
    broadcastWS({ type: 'all_modules', modules: modules.map(m => ({ id: m.getModuleName(), config: m.config })) });
    res.json({ success: true });
  } catch (err) {
    console.error('Failed to remove interaction:', err);
    res.status(500).json({ error: 'Failed to remove interaction' });
  }
});

app.post('/api/interactions/update', async (req: Request, res: Response) => {
  const { oldInteraction, newInteraction } = req.body;
  try {
    const configPath = path.join(__dirname, '../../config/interactions/interactions.json');
    const configData = JSON.parse(fs.readFileSync(configPath, 'utf-8'));
    // Replace the old interaction with the new one
    configData.interactions = configData.interactions.map((interaction: any) =>
      (interaction.input.module === oldInteraction.input.module &&
        interaction.output.module === oldInteraction.output.module)
        ? newInteraction : interaction
    );
    fs.writeFileSync(configPath, JSON.stringify(configData, null, 2));
    // Update message router
    messageRouter.updateInteraction(oldInteraction, newInteraction, modules);
    broadcastWS({ type: 'all_modules', modules: modules.map(m => ({ id: m.getModuleName(), config: m.config })) });
    res.json({ success: true });
  } catch (err) {
    console.error('Failed to update interaction:', err);
    res.status(500).json({ error: 'Failed to update interaction' });
  }
});

app.get('/api/interactions', (req: Request, res: Response) => {
  try {
    const configPath = path.join(__dirname, '../../config/interactions/interactions.json');
    const configData = JSON.parse(fs.readFileSync(configPath, 'utf-8'));
    res.json(configData.interactions || []);
  } catch (err) {
    res.status(500).json({ error: 'Failed to load interactions' });
  }
});

// Audio file directory and endpoints (must be before static file serving)
const audioDir = path.resolve(__dirname, '../src/modules/audio_output/assets/audio');
if (!fs.existsSync(audioDir)) fs.mkdirSync(audioDir, { recursive: true });
const upload = multer({ dest: audioDir });

// List audio files
app.get('/api/audio_files', (req: Request, res: Response) => {
  console.log('DEBUG: GET /api/audio_files called');
  console.log('DEBUG: audioDir path:', audioDir);
  fs.readdir(audioDir, (err, files) => {
    if (err) {
      console.error('ERROR: Failed to list audio files:', err);
      return res.status(500).json({ error: 'Failed to list audio files' });
    }
    console.log('DEBUG: All files found:', files);
    const audioFiles = files.filter(f => f.endsWith('.wav') || f.endsWith('.mp3'));
    console.log('DEBUG: Filtered audio files:', audioFiles);
    res.json(audioFiles);
  });
});

// Upload audio file
app.post('/api/audio_files', upload.single('file'), (req: Request, res: Response) => {
  console.log('DEBUG: POST /api/audio_files called');
  if (!req.file) {
    console.error('ERROR: No file uploaded');
    return res.status(400).json({ error: 'No file uploaded' });
  }
  const destPath = path.join(audioDir, req.file.originalname);
  console.log('DEBUG: Upload attempt for file:', req.file.originalname);
  if (fs.existsSync(destPath)) {
    console.warn('WARNING: File already exists:', req.file.originalname);
    return res.status(409).json({ error: 'File already exists' });
  }
  try {
    fs.renameSync(req.file.path, destPath);
    console.log('DEBUG: File saved as:', destPath);
    broadcastWS({ type: 'audio_files_update' });
    res.json({ success: true, filename: req.file.originalname });
  } catch (err) {
    console.error('ERROR: Failed to save uploaded file:', err);
    return res.status(500).json({ error: 'Failed to save file' });
  }
});

// --- All API endpoints and audio file logic above this line ---

// --- Serve frontend static files (should be last!) ---
const frontendDist = path.join(__dirname, '../../web-frontend/dist');

// SPA fallback: serve index.html for any non-API route
app.get('*', (req: Request, res: Response) => {
  if (req.path.startsWith('/api') || req.path.startsWith('/modules')) {
    return res.status(404).json({ error: 'API endpoint not found' });
  }
  // Serve static files for non-API routes
  const filePath = path.join(frontendDist, req.path);
  if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
    res.sendFile(filePath);
  } else {
    // Fallback to index.html for SPA routing
    res.sendFile(path.join(frontendDist, 'index.html'));
  }
});

const PORT = Number(process.env.PORT) || 8000;
const HOST = '0.0.0.0';
server.listen(PORT, HOST, () => {
  logger.log(`Server started on http://${HOST}:${PORT}`, 'System');
}); 