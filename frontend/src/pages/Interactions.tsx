import { useState, useEffect } from 'react';
import { Box, Button, Typography, Paper, Select, MenuItem, FormControl, InputLabel, Snackbar, Alert, Divider } from '@mui/material';
import ModuleSettingsForm from '../components/ModuleSettingsForm';
import { useModulesStore } from '../state/useModulesStore';
import DeleteIcon from '@mui/icons-material/Delete';
import IconButton from '@mui/material/IconButton';
import ReactFlow, { Background, Controls, MiniMap, Handle, Position } from 'react-flow-renderer';
import type { Node, Edge, NodeProps } from 'react-flow-renderer';
import { useRef } from 'react';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';

const INTERACTION_DRAFT_KEY = 'interactionDraft';

function buildNodeLabel(module: string, config: any) {
  let label = module;
  if (config && typeof config === 'object') {
    for (const [key, value] of Object.entries(config)) {
      label += `\n${key}: ${String(value)}`;
    }
  }
  return label;
}

// Custom node with trash can
function ModuleNode({ id, data }: NodeProps) {
  const [countdown, setCountdown] = useState<string>('');
  
  // Determine if this is an audio_output node
  const isAudioOutput = data.label.startsWith('audio_output');
  // Determine if this is a time_input node
  const isTimeInput = data.label.startsWith('time_input');
  
  // Fetch countdown for time input modules
  useEffect(() => {
    if (isTimeInput) {
      const fetchCountdown = async () => {
        try {
          // Extract module name from node ID
          const match = id.match(/^(input|output)-(.+?)-({.*})$/);
          if (!match) return;
          const [, , module] = match;
          
          // Map module directory names to manifest names for API calls
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
          
          const apiModuleName = moduleNameMap[module] || module;
          
          // Extract config from node ID to pass to the countdown API
          const configMatch = id.match(/^(input|output)-(.+?)-({.*})$/);
          let config = null;
          if (configMatch) {
            try {
              config = JSON.parse(configMatch[3]);
            } catch (err) {
              console.error('Failed to parse config from node ID:', err);
            }
          }
          
          const url = config 
            ? `/api/modules/${encodeURIComponent(apiModuleName)}/countdown?config=${encodeURIComponent(JSON.stringify(config))}`
            : `/api/modules/${encodeURIComponent(apiModuleName)}/countdown`;
            
          const response = await fetch(url);
          if (response.ok) {
            const data = await response.json();
            setCountdown(data.countdown);
          }
        } catch (error) {
          console.error('Failed to fetch countdown:', error);
        }
      };
      
      fetchCountdown();
      // Update countdown every second
      const interval = setInterval(fetchCountdown, 1000);
      return () => clearInterval(interval);
    }
  }, [id, isTimeInput]);
  
  const handlePlay = async () => {
    // Extract config from nodeId
    const match = id.match(/^(input|output)-(.+?)-({.*})$/);
    if (!match) return;
    const [, , module, configStr] = match;
    let config;
    try { config = JSON.parse(configStr); } catch { return; }
    console.log('[Audio]', 'Manual play triggered for:', config);
    await fetch('/api/modules/audio_output/trigger', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ config }),
    });
  };
  
  return (
    <div style={{ minWidth: 180, padding: 8, border: '2px solid #fff', borderRadius: 6, background: '#222', position: 'relative' }}>
      <div style={{ whiteSpace: 'pre-line', fontSize: 13, color: '#fff' }}>{data.label}</div>
      
      {/* Countdown display for time input modules */}
      {isTimeInput && countdown && (
        <div style={{ 
          marginTop: 4, 
          padding: '2px 6px', 
          background: '#444', 
          borderRadius: 3, 
          fontSize: 11, 
          color: '#fff',
          border: '1px solid #666'
        }}>
          Countdown: {countdown}
        </div>
      )}
      
      {/* Icon row: play (if audio) and delete, aligned top right */}
      <div style={{ position: 'absolute', top: 2, right: 2, display: 'flex', gap: 4 }}>
        {isAudioOutput && (
          <IconButton
            size="small"
            color="primary"
            onClick={handlePlay}
          >
            <PlayArrowIcon fontSize="small" />
          </IconButton>
        )}
        <IconButton
          size="small"
          color="error"
          onClick={() => data.onDelete(id)}
        >
          <DeleteIcon fontSize="small" />
        </IconButton>
      </div>
      <Handle type="target" position={Position.Left} style={{ background: '#fff' }} isConnectable={false} />
      <Handle type="source" position={Position.Right} style={{ background: '#fff' }} isConnectable={false} />
    </div>
  );
}

function InteractionsGraph({ interactions, onDeleteModule }: { interactions: any[], onDeleteModule: (nodeId: string) => void }) {
  // Build unique nodes and edges
  const nodesMap = new Map<string, Node>();
  const edges: Edge[] = [];
  interactions.forEach((interaction, idx) => {
    const inputId = `input-${interaction.input.module}-${JSON.stringify(interaction.input.config)}`;
    const outputId = `output-${interaction.output.module}-${JSON.stringify(interaction.output.config)}`;
    if (!nodesMap.has(inputId)) {
      nodesMap.set(inputId, {
        id: inputId,
        type: 'moduleNode',
        data: {
          label: buildNodeLabel(interaction.input.module, interaction.input.config),
          onDelete: onDeleteModule,
        },
        position: { x: 100, y: 100 + nodesMap.size * 100 },
      });
    }
    if (!nodesMap.has(outputId)) {
      nodesMap.set(outputId, {
        id: outputId,
        type: 'moduleNode',
        data: {
          label: buildNodeLabel(interaction.output.module, interaction.output.config),
          onDelete: onDeleteModule,
        },
        position: { x: 400, y: 100 + nodesMap.size * 100 },
      });
    }
    edges.push({
      id: `e-${inputId}-${outputId}`,
      source: inputId,
      target: outputId,
      animated: true,
      style: { stroke: '#1976d2', strokeWidth: 2 },
    });
  });
  const nodes = Array.from(nodesMap.values());
  return (
    <div style={{ height: 400, width: '100%' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        fitView
        nodeTypes={{ moduleNode: ModuleNode }}
      >
        <MiniMap
          nodeColor={() => '#fff'}
          style={{ background: '#000' }}
        />
        <Controls />
        <Background />
      </ReactFlow>
    </div>
  );
}

// Add a helper to validate config against manifest fields
function validateConfig(config: any, manifest: any): string[] {
  const errors: string[] = [];
  if (!manifest || !manifest.fields) return errors;
  for (const field of manifest.fields) {
    const value = config[field.name];
    if (value === undefined || value === null || value === '') {
      errors.push(`${field.label || field.name} is required`);
      continue;
    }
    if (field.type === 'number' && isNaN(Number(value))) {
      errors.push(`${field.label || field.name} must be a number`);
    }
    if (field.type === 'time') {
      // Accept HH:MM or HH:MM:SS
      if (!/^\d{1,2}:\d{2}(:\d{2})?$/.test(value)) {
        errors.push(`${field.label || field.name} must be in HH:MM or HH:MM:SS format`);
      }
    }
    // Add more type checks as needed
  }
  return errors;
}

const Interactions = () => {
  // Load draft from localStorage if present
  const draft = (() => {
    try {
      return JSON.parse(localStorage.getItem(INTERACTION_DRAFT_KEY) || 'null') || {};
    } catch {
      return {};
    }
  })();

  const [adding, setAdding] = useState(false);
  const [inputModuleName, setInputModuleName] = useState(draft.inputModuleName || '');
  const [outputModuleName, setOutputModuleName] = useState(draft.outputModuleName || '');
  const [inputConfig, setInputConfig] = useState<any>(draft.inputConfig || null);
  const [outputConfig, setOutputConfig] = useState<any>(draft.outputConfig || null);
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({ open: false, message: '', severity: 'success' });
  const [registering, setRegistering] = useState(false);
  const [interactions, setInteractions] = useState<any[]>([]);

  const availableModules = useModulesStore(state => state.availableModules);
  const fetchAvailableModules = useModulesStore(state => state.fetchAvailableModules);

  const inputModules = availableModules.filter((m: any) => m.manifest?.type === 'input');
  const outputModules = availableModules.filter((m: any) => m.manifest?.type === 'output');

  const inputManifest = inputModules.find((m: any) => m.name === inputModuleName)?.manifest;
  const outputManifest = outputModules.find((m: any) => m.name === outputModuleName)?.manifest;

  // Save draft to localStorage on every change
  useEffect(() => {
    localStorage.setItem(
      INTERACTION_DRAFT_KEY,
      JSON.stringify({ inputModuleName, outputModuleName, inputConfig, outputConfig })
    );
  }, [inputModuleName, outputModuleName, inputConfig, outputConfig]);

  // Handler for settings form changes
  const handleInputConfigChange = (config: any) => setInputConfig(config);
  const handleOutputConfigChange = (config: any) => setOutputConfig(config);

  const handleInputModuleChange = (moduleName: string) => {
    setInputModuleName(moduleName);
    // Try to restore config for this module from draft
    const draft = (() => {
      try {
        return JSON.parse(localStorage.getItem(INTERACTION_DRAFT_KEY) || 'null') || {};
      } catch {
        return {};
      }
    })();
    setInputConfig(
      moduleName && draft.inputModuleName === moduleName && draft.inputConfig
        ? draft.inputConfig
        : {}
    );
  };
  const handleOutputModuleChange = (moduleName: string) => {
    setOutputModuleName(moduleName);
    // Try to restore config for this module from draft
    const draft = (() => {
      try {
        return JSON.parse(localStorage.getItem(INTERACTION_DRAFT_KEY) || 'null') || {};
      } catch {
        return {};
      }
    })();
    setOutputConfig(
      moduleName && draft.outputModuleName === moduleName && draft.outputConfig
        ? draft.outputConfig
        : {}
    );
  };

  // Register button enabled if both modules and configs are set
  const canRegister = inputModuleName && outputModuleName && inputConfig && outputConfig;

  const fetchInteractions = async () => {
    const res = await fetch('/api/interactions');
    const data = await res.json();
    setInteractions(data);
  };

  useEffect(() => {
    fetchAvailableModules();
    fetchInteractions();
  }, [fetchAvailableModules]);

  const clearDraft = () => {
    localStorage.removeItem(INTERACTION_DRAFT_KEY);
    setInputModuleName('');
    setOutputModuleName('');
    setInputConfig(null);
    setOutputConfig(null);
  };

  const handleRegister = async () => {
    setRegistering(true);
    // Find manifests for input and output modules
    const inputManifest = inputModules.find((m: any) => m.name === inputModuleName)?.manifest;
    const outputManifest = outputModules.find((m: any) => m.name === outputModuleName)?.manifest;
    const inputErrors = validateConfig(inputConfig, inputManifest);
    const outputErrors = validateConfig(outputConfig, outputManifest);
    if (inputErrors.length > 0 || outputErrors.length > 0) {
      let message = '';
      if (inputErrors.length > 0) message += `Input module (${inputManifest?.name || inputModuleName}):\n- ${inputErrors.join('\n- ')}\n`;
      if (outputErrors.length > 0) message += `Output module (${outputManifest?.name || outputModuleName}):\n- ${outputErrors.join('\n- ')}`;
      setSnackbar({ open: true, message, severity: 'error' });
      setRegistering(false);
      return;
    }
    try {
      const res = await fetch('/api/interactions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          input: { module: inputModuleName, config: inputConfig },
          output: { module: outputModuleName, config: outputConfig },
        }),
      });
      if (!res.ok) throw new Error('Failed to register interaction');
      setSnackbar({ open: true, message: 'Interaction registered!', severity: 'success' });
      // Reset form and clear draft
      setAdding(false);
      clearDraft();
      fetchInteractions();
    } catch (err: any) {
      setSnackbar({ open: true, message: err.message || 'Error', severity: 'error' });
    } finally {
      setRegistering(false);
    }
  };

  const handleDeleteInteraction = async (interaction: any) => {
    if (!window.confirm('Are you sure you want to delete this interaction?')) return;
    try {
      const res = await fetch('/api/interactions/remove', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(interaction),
      });
      if (!res.ok) throw new Error('Failed to delete interaction');
      setSnackbar({ open: true, message: 'Interaction deleted!', severity: 'success' });
      fetchInteractions();
    } catch (err: any) {
      setSnackbar({ open: true, message: err.message || 'Error', severity: 'error' });
    }
  };

  const handleDeleteModule = async (nodeId: string) => {
    // Find the module name and config from the nodeId
    const match = nodeId.match(/^(input|output)-(.+?)-({.*})$/);
    if (!match) return;
    const [, type, module, configStr] = match;
    let config;
    try { config = JSON.parse(configStr); } catch { return; }
    // Find all interactions that use this module/config
    const toDelete = interactions.filter(interaction =>
      (interaction.input.module === module && JSON.stringify(interaction.input.config) === JSON.stringify(config)) ||
      (interaction.output.module === module && JSON.stringify(interaction.output.config) === JSON.stringify(config))
    );
    for (const interaction of toDelete) {
      await fetch('/api/interactions/remove', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(interaction),
      });
    }
    fetchInteractions();
  };

  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h4" gutterBottom>Interactions</Typography>
      <Button variant="contained" onClick={() => setAdding(true)} sx={{ mb: 2 }}>Add New Interaction</Button>
      {adding && (
        <Paper sx={{ p: 2, mb: 2 }}>
          <Box
            sx={{
              display: 'flex',
              flexDirection: { xs: 'column', md: 'row' },
              gap: 3,
              alignItems: 'flex-start',
            }}
          >
            <Box sx={{ flex: 1, minWidth: 0 }}>
              <Typography variant="h6">Input Module</Typography>
              <FormControl fullWidth size="small" sx={{ mb: 2 }}>
                <InputLabel id="input-module-label">Select Input Module</InputLabel>
                <Select
                  labelId="input-module-label"
                  value={inputModuleName}
                  label="Select Input Module"
                  onChange={e => handleInputModuleChange(e.target.value)}
                >
                  <MenuItem value=""><em>None</em></MenuItem>
                  {inputModules.map((mod: any) => (
                    <MenuItem key={mod.name} value={mod.name}>{mod.manifest?.name || mod.name}</MenuItem>
                  ))}
                </Select>
              </FormControl>
              {inputManifest && (
                <ModuleSettingsForm
                  manifest={inputManifest}
                  config={inputConfig || {}}
                  moduleId={inputModuleName}
                  onConfigChange={handleInputConfigChange}
                  persistOnChange={false}
                />
              )}
            </Box>
            <Box sx={{ flex: 1, minWidth: 0 }}>
              <Typography variant="h6">Output Module</Typography>
              <FormControl fullWidth size="small" sx={{ mb: 2 }}>
                <InputLabel id="output-module-label">Select Output Module</InputLabel>
                <Select
                  labelId="output-module-label"
                  value={outputModuleName}
                  label="Select Output Module"
                  onChange={e => handleOutputModuleChange(e.target.value)}
                >
                  <MenuItem value=""><em>None</em></MenuItem>
                  {outputModules.map((mod: any) => (
                    <MenuItem key={mod.name} value={mod.name}>{mod.manifest?.name || mod.name}</MenuItem>
                  ))}
                </Select>
              </FormControl>
              {outputManifest && (
                <ModuleSettingsForm
                  manifest={outputManifest}
                  config={outputConfig || {}}
                  moduleId={outputModuleName}
                  onConfigChange={handleOutputConfigChange}
                  persistOnChange={false}
                />
              )}
            </Box>
          </Box>
          {canRegister && (
            <Box sx={{ mt: 2, textAlign: 'right' }}>
              <Button variant="contained" color="primary" onClick={handleRegister} disabled={registering}>
                {registering ? 'Registering...' : 'Register'}
              </Button>
            </Box>
          )}
        </Paper>
      )}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={3000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert severity={snackbar.severity} sx={{ width: '100%' }}>{snackbar.message}</Alert>
      </Snackbar>
      <Divider sx={{ my: 3 }} />
      <Typography variant="h5" gutterBottom>Interaction Map</Typography>
      {/* Replace the list with the dynamic graph */}
      <InteractionsGraph interactions={interactions} onDeleteModule={handleDeleteModule} />
    </Box>
  );
};

export default Interactions; 