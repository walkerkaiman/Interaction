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

// Catch-all API log (before all API endpoints)
app.use('/api', (req, res, next) => {
  console.log('DEBUG: API request received:', req.method, req.originalUrl);
  next();
});

// --- Load config and instantiate modules ---
const configPath = path.join(__dirname, '../../config/interactions/interactions.json');
let interactions: any[] = [];
let modules: any[] = [];

// Initialize modules asynchronously
(async () => {
  try {
    const config = JSON.parse(fs.readFileSync(configPath, 'utf-8'));
    interactions = config.interactions || [];
    modules = moduleLoader.loadModulesFromConfig(configPath);
    
    // Start all loaded modules
    for (const module of modules) {
      try {
        await module.start();
        logger.log(`Started module: ${module.getModuleName()}`, 'System');
      } catch (err) {
        logger.log(`Failed to start module ${module.getModuleName()}: ${err}`, 'Error');
      }
    }
    
    logger.log(`Loaded and started ${modules.length} modules from config`, 'System');
  } catch (e) {
    logger.log('Failed to load config: ' + e, 'Error');
  }
})();

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
          ws.send(JSON.stringify({ type: 'all_modules', modules: modules.map(m => ({ id: m.getModuleName(), config: m.getConfig() })) }));
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

app.get('/api/log_levels', (req, res) => {
  res.json([
    'Error',
    'System', 
    'Audio',
    'DMX',
    'Frames',
    'OSC',
    'Serial',
    'Time',
    'Performance'
  ]);
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
  const wikiDir = path.join(__dirname, '../../frontend/module_wikis');
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

// Get countdown info for time input modules
app.get('/api/modules/:id/countdown', (req: Request, res: Response) => {
  const { id } = req.params;
  const configParam = req.query.config as string;
  
  console.log('Countdown request for module ID:', id, 'Config:', configParam);
  
  let targetConfig = null;
  if (configParam) {
    try {
      targetConfig = JSON.parse(configParam);
    } catch (err) {
      console.log('Invalid config parameter:', configParam);
      return res.status(400).json({ error: 'Invalid config parameter' });
    }
  }
  
  // Try to find module by manifest name first, then by module directory name
  let mod = modules.find(m => m.getModuleName() === id);
  
  // If not found by manifest name, try to find by module directory name
  if (!mod) {
    // Map common module directory names to their manifest names
    const moduleNameMap: { [key: string]: string } = {
      'time_input': 'Time Input',
      'audio_output': 'Audio Output',
      'dmx_output': 'DMX Output',
      'osc_input': 'OSC Input',
      'osc_output': 'OSC Output',
      'http_input': 'HTTP Input',
      'http_output': 'HTTP Output',
      'serial_input': 'Serial Input',
      'frames_input': 'Frames Input'
    };
    
    const manifestName = moduleNameMap[id];
    console.log('Looking for manifest name:', manifestName);
    if (manifestName) {
      mod = modules.find(m => m.getModuleName() === manifestName);
    }
  }
  
  if (!mod) {
    console.log('Module not found for ID:', id);
    return res.status(404).json({ error: 'Module not found' });
  }
  
  // If we have a target config, find the specific module instance with that config
  if (targetConfig) {
    const originalMod = mod; // Store the original module for comparison
    mod = modules.find(m => 
      m.getModuleName() === originalMod.getModuleName() && 
      JSON.stringify(m.getConfig()) === JSON.stringify(targetConfig)
    );
    
    if (!mod) {
      console.log('Module with specific config not found');
      console.log('Looking for module:', originalMod.getModuleName(), 'with config:', JSON.stringify(targetConfig));
      console.log('Available modules:', modules.map(m => ({ name: m.getModuleName(), config: m.getConfig() })));
      return res.status(404).json({ error: 'Module with specific config not found' });
    }
  }
  
  console.log('Found module:', mod.getModuleName(), 'Constructor:', mod.constructor.name, 'Config:', mod.getConfig());
  
  // Check if this is a time input module
  if (mod.constructor.name === 'TimeInputModule' && typeof mod.getCountdownInfo === 'function') {
    const countdownInfo = mod.getCountdownInfo();
    console.log('Countdown info:', countdownInfo);
    res.json(countdownInfo);
  } else {
    console.log('Module does not support countdown');
    res.status(400).json({ error: 'Module does not support countdown' });
  }
});

// Start all modules manually
app.post('/api/modules/start', async (req: Request, res: Response) => {
  try {
    console.log('Starting all modules...');
    for (const module of modules) {
      try {
        await module.start();
        console.log(`Started module: ${module.getModuleName()}`);
      } catch (err) {
        console.log(`Failed to start module ${module.getModuleName()}: ${err}`);
      }
    }
    res.json({ success: true, message: `Started ${modules.length} modules` });
  } catch (err) {
    console.error('Failed to start modules:', err);
    res.status(500).json({ error: 'Failed to start modules' });
  }
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
        Object.assign(mod.getConfig(), newSettings);
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
  broadcastWS({ type: 'module_update', moduleId: id, newState: mod.getConfig() });
  mod.unlock();
  broadcastWS({ type: 'module_unlock', moduleId: id });
  res.json({ success: true, newState: mod.getConfig() });
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

// --- Serve waveform SVG for audio_output ---
app.get('/api/module_waveform/:module', async (req: Request, res: Response) => {
  const moduleName = req.params.module;
  if (moduleName !== 'audio_output') return res.status(404).send('Not found');

  // Get the filename from the query
  const fileName = req.query.file as string;
  if (!fileName) return res.status(400).send('No file specified');

  // Path to the audio file
  const audioDir = path.resolve(__dirname, './modules/audio_output/assets/audio');
  const audioFilePath = path.join(audioDir, fileName);

  // Path to the waveform image
  const imageDir = path.resolve(__dirname, './modules/audio_output/assets/image');
  const waveformFile = path.join(imageDir, fileName + '.waveform.svg');

  // Generate waveform if it doesn't exist
  if (!fs.existsSync(waveformFile)) {
    try {
      const { AudioOutputModule } = require('./modules/audio_output');
      const tempModule = new AudioOutputModule({}, (msg: string) => console.log(msg));
      await tempModule.generateWaveform(audioFilePath);
    } catch (err) {
      console.error('Failed to generate waveform:', err);
      return res.status(500).send('Failed to generate waveform');
    }
  }

  if (!fs.existsSync(waveformFile)) {
    return res.status(404).send('Waveform not found');
  }

  res.setHeader('Content-Type', 'image/svg+xml');
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
      await newInput.start(); // Start the input module
      modules.push(newInput);
    }
    if (OutputClass) {
      newOutput = new OutputClass(outputConfig, logger.log.bind(logger));
      await newOutput.start(); // Start the output module
      modules.push(newOutput);
    }
    // Add to message router
    messageRouter.addInteraction(newInteraction, modules);
    // Broadcast new state to all UIs
    broadcastWS({ type: 'all_modules', modules: modules.map(m => ({ id: m.getModuleName(), config: m.getConfig() })) });
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
    // Stop and remove module instances - match by both module name and config
    console.log(`Removing interaction: ${interactionToRemove.input.module} -> ${interactionToRemove.output.module}`);
    console.log(`Current modules: ${modules.map(m => `${m.getModuleName()}:${JSON.stringify(m.getConfig())}`).join(', ')}`);
    
    // Map module directory names to manifest names for matching
    const moduleNameMap: { [key: string]: string } = {
      'time_input': 'Time Input',
      'audio_output': 'Audio Output',
      'dmx_output': 'DMX Output',
      'osc_input': 'OSC Input',
      'osc_output': 'OSC Output',
      'http_input': 'HTTP Input',
      'http_output': 'HTTP Output',
      'serial_input': 'Serial Input',
      'frames_input': 'Frames Input'
    };
    
    const inputManifestName = moduleNameMap[interactionToRemove.input.module] || interactionToRemove.input.module;
    const outputManifestName = moduleNameMap[interactionToRemove.output.module] || interactionToRemove.output.module;
    
    const inputIdx = modules.findIndex(m => 
      m.getModuleName() === inputManifestName && 
      JSON.stringify(m.getConfig()) === JSON.stringify(interactionToRemove.input.config)
    );
    if (inputIdx !== -1) {
      console.log(`Stopping and removing input module at index ${inputIdx}: ${modules[inputIdx].getModuleName()}`);
      if (typeof modules[inputIdx].stop === 'function') {
        await modules[inputIdx].stop();
      }
      modules.splice(inputIdx, 1);
    } else {
      console.log(`Input module not found: ${inputManifestName} with config ${JSON.stringify(interactionToRemove.input.config)}`);
    }
    
    const outputIdx = modules.findIndex(m => 
      m.getModuleName() === outputManifestName && 
      JSON.stringify(m.getConfig()) === JSON.stringify(interactionToRemove.output.config)
    );
    if (outputIdx !== -1) {
      console.log(`Stopping and removing output module at index ${outputIdx}: ${modules[outputIdx].getModuleName()}`);
      if (typeof modules[outputIdx].stop === 'function') {
        await modules[outputIdx].stop();
      }
      modules.splice(outputIdx, 1);
    } else {
      console.log(`Output module not found: ${outputManifestName} with config ${JSON.stringify(interactionToRemove.output.config)}`);
    }
    
    console.log(`Modules after removal: ${modules.map(m => m.getModuleName()).join(', ')}`);
    broadcastWS({ type: 'all_modules', modules: modules.map(m => ({ id: m.getModuleName(), config: m.getConfig() })) });
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
    broadcastWS({ type: 'all_modules', modules: modules.map(m => ({ id: m.getModuleName(), config: m.getConfig() })) });
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

const { execSync } = require('child_process');

function convertWavToPcm(inputPath: string, outputPath: string): boolean {
  try {
    execSync(`ffmpeg -y -i "${inputPath}" -acodec pcm_s16le -ar 44100 "${outputPath}"`);
    return true;
  } catch (err: any) {
    console.error('ffmpeg conversion failed:', err);
    return false;
  }
}

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
app.post('/api/audio_files', upload.single('file'), async (req: Request, res: Response) => {
  console.log('DEBUG: POST /api/audio_files called');
  if (!req.file) {
    console.error('ERROR: No file uploaded');
    return res.status(400).json({ error: 'No file uploaded' });
  }
  const srcAudioDir = path.resolve(__dirname, '../src/modules/audio_output/assets/audio');
  const distAudioDir = path.resolve(__dirname, './modules/audio_output/assets/audio');
  if (!fs.existsSync(srcAudioDir)) fs.mkdirSync(srcAudioDir, { recursive: true });
  if (!fs.existsSync(distAudioDir)) fs.mkdirSync(distAudioDir, { recursive: true });
  const destPathSrc = path.join(srcAudioDir, req.file.originalname);
  const destPathDist = path.join(distAudioDir, req.file.originalname);
  console.log('DEBUG: Upload attempt for file:', req.file.originalname);
  if (fs.existsSync(destPathSrc) || fs.existsSync(destPathDist)) {
    console.warn('WARNING: File already exists:', req.file.originalname);
    return res.status(409).json({ error: 'File already exists' });
  }
  try {
    // Move uploaded file to src
    fs.renameSync(req.file.path, destPathSrc);
    // Try to generate waveform to check if conversion is needed
    let needsConversion = false;
    try {
      const { AudioOutputModule } = require('./modules/audio_output');
      const tempModule = new AudioOutputModule({}, (msg: string) => console.log(msg));
      await tempModule.generateWaveform(destPathSrc);
    } catch (err: any) {
      needsConversion = true;
    }
    if (needsConversion) {
      const tempPath = destPathSrc + '.converted.wav';
      if (convertWavToPcm(destPathSrc, tempPath)) {
        fs.renameSync(tempPath, destPathSrc);
        // Optionally, regenerate waveform here if needed
      }
    }
    // Copy to dist
    fs.copyFileSync(destPathSrc, destPathDist);
    console.log('DEBUG: File saved as:', destPathSrc, 'and copied to:', destPathDist);
    broadcastWS({ type: 'audio_files_update' });
    res.json({ success: true, filename: req.file.originalname });
  } catch (err: any) {
    console.error('ERROR: Failed to save uploaded file:', err);
    return res.status(500).json({ error: 'Failed to save file' });
  }
});

// --- All API endpoints and audio file logic above this line ---

function normalizeModuleName(name: string) {
  return name.toLowerCase().replace(/ /g, '_');
}
// --- Manual trigger endpoint for all output modules ---
app.post('/api/modules/:module/trigger', async (req: Request, res: Response) => {
  const moduleName = req.params.module;
  const config = req.body.config;
  console.log('Trigger request:', moduleName, config);
  const mod = modules.find(m => {
    console.log('Comparing to:', m.getModuleName(), m.getConfig());
    return normalizeModuleName(m.getModuleName()) === normalizeModuleName(moduleName) && JSON.stringify(m.getConfig()) === JSON.stringify(config);
  });
  console.log('Found module:', mod ? 'YES' : 'NO');
  if (!mod || typeof mod.manualTrigger !== 'function') {
    console.log('Output module not found or cannot be triggered');
    return res.status(404).json({ error: 'Output module not found or cannot be triggered' });
  }
  try {
    await mod.manualTrigger();
    console.log('manualTrigger called successfully');
    res.json({ success: true });
  } catch (err) {
    console.error('manualTrigger error:', err);
    res.status(500).json({ error: 'Failed to trigger output module' });
  }
});

// --- Serve frontend static files (should be last!) ---
const frontendDist = path.join(__dirname, '../../frontend/dist');

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

// Ensure all audio files in dist have a waveform SVG in dist image dir
const distAudioDir = path.resolve(__dirname, './modules/audio_output/assets/audio');
const distImageDir = path.resolve(__dirname, './modules/audio_output/assets/image');
if (!fs.existsSync(distImageDir)) fs.mkdirSync(distImageDir, { recursive: true });

(async () => {
  try {
    const { AudioOutputModule } = require('./modules/audio_output');
    const tempModule = new AudioOutputModule({}, (msg: string) => console.log(msg));
    const audioFiles = fs.readdirSync(distAudioDir).filter((f: string) => f.endsWith('.wav') || f.endsWith('.mp3'));
    for (const audioFile of audioFiles) {
      const audioPath = path.join(distAudioDir, audioFile);
      const imagePath = path.join(distImageDir, audioFile + '.waveform.svg');
      if (!fs.existsSync(imagePath)) {
        let success = false;
        try {
          await tempModule.generateWaveform(audioPath);
          console.log(`Generated waveform for ${audioFile}`);
          success = true;
        } catch (err: any) {
          console.warn(`Waveform decode failed for ${audioFile}: ${err.message}, attempting conversion...`);
          const tempPath = audioPath + '.converted.wav';
          if (convertWavToPcm(audioPath, tempPath)) {
            try {
              await tempModule.generateWaveform(tempPath);
              fs.renameSync(tempPath, audioPath);
              console.log(`Converted and generated waveform for ${audioFile}`);
              success = true;
            } catch (err2: any) {
              console.error(`Failed after conversion for ${audioFile}:`, err2);
              if (fs.existsSync(tempPath)) fs.unlinkSync(tempPath);
            }
          }
        }
        if (!success) {
          console.error(`Failed to process ${audioFile}, skipping.`);
        }
      }
    }
  } catch (err: any) {
    console.error('Startup waveform check failed:', err);
  }
})();

server.listen(PORT, HOST, () => {
  logger.log(`Server started on http://${HOST}:${PORT}`, 'System');
  console.log('=== Backend server ready and listening on port', PORT, '===');
}); 