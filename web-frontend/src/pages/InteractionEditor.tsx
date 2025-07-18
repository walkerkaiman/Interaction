import React, { useEffect, useState, useRef } from 'react';
import {
  Box, Typography, Paper, Button, Select, MenuItem, TextField, IconButton, CircularProgress, Alert,
  Slider, InputAdornment, FormControl, InputLabel
} from '@mui/material';
import { Grid } from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';
import SaveIcon from '@mui/icons-material/Save';
import { fetchConfig, updateConfig, fetchModules, deleteInteraction, fetchModuleInstances, browseAudioFiles } from '../api/api';
import axios from 'axios';
import { connectWebSocket, addMessageHandler, removeMessageHandler } from '../api/ws';
import FileSelector from '../components/FileSelector';

interface ModuleManifestField {
  name: string;
  type: string;
  default?: any;
  label?: string;
  description?: string;
  min?: number;
  max?: number;
}

interface ModuleManifest {
  fields: ModuleManifestField[];
  supports_manual_trigger?: boolean;
}

interface Module {
  id: string;
  name: string;
  type: string;
  [key: string]: any;
}

interface Interaction {
  input: {
    module: string;
    config: Record<string, any>;
  };
  output: {
    module: string;
    config: Record<string, any>;
  };
}

const fetchManifest = async (moduleId: string) => {
  try {
    const timestamp = Date.now();
    const response = await fetch(`/modules/${moduleId}/manifest.json?t=${timestamp}`);
    if (response.ok) {
      return await response.json();
    }
  } catch (e) {
    console.error(`Failed to load manifest for moduleId:`, moduleId, e);
  }
  return null;
};

const InteractionEditor: React.FC = () => {
  const [interactions, setInteractions] = useState<Interaction[]>([]);
  const [modules, setModules] = useState<Module[]>([]);
  const [manifests, setManifests] = useState<Record<string, ModuleManifest>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [deleting, setDeleting] = useState<number | null>(null); // Track which interaction is being deleted
  // Add state for real-time clock values per interaction
  const [clockTimes, setClockTimes] = useState<Record<number, { current_time: string; countdown: string }>>({});
  // Track instance_id to interaction index mapping
  const [instanceIdMapping, setInstanceIdMapping] = useState<Record<string, number>>({});
  // Add state for available audio files
  const [audioFiles, setAudioFiles] = useState<Array<{name: string, path: string, size: number}>>();
  const [dirtyStates, setDirtyStates] = useState<Record<number, { input: boolean; output: boolean }>>({});
  const wsRef = useRef<WebSocket | null>(null);
  // Add state for original interactions
  const [originalInteractions, setOriginalInteractions] = useState<Interaction[]>([]);

  // Load modules and interactions
  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const [modulesArr, config, audioFilesData] = await Promise.all([
          fetchModules(),
          fetchConfig(),
          browseAudioFiles()
        ]);
        setModules(modulesArr);
        setInteractions(config.interactions || []);
        setOriginalInteractions(config.interactions || []); // <-- update originalInteractions
        setAudioFiles(audioFilesData.files || []);
        // Preload manifests for all modules
        const allModuleIds = Array.from(new Set([
          ...modulesArr.map(m => m.id),
          ...((config.interactions || []).flatMap((i: Interaction) => [i.input.module, i.output.module]))
        ]));
        const manifestEntries = await Promise.all(
          allModuleIds.map(async id => {
            const manifest = await fetchManifest(id);
            // Debug logging for audio_output module
            if (id === 'audio_output') {           console.log('[DEBUG] audio_output manifest received:', manifest);
              console.log('[DEBUG] audio_output fields:', manifest?.fields);
              // Log each field individually to see the actual types
              if (manifest?.fields) {
                manifest.fields.forEach((field: any, index: number) => {
                  console.log(`[DEBUG] audio_output field ${index}:`, field);
                });
              }
            }
            return [id, manifest];
          })
        );
        setManifests(Object.fromEntries(manifestEntries));
      } catch (e: any) {
        setError(e.message || 'Failed to load data');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  useEffect(() => {
    // Connect websocket and add message handler
    wsRef.current = connectWebSocket();
    
    const messageHandler = (data: any) => {
      // Check if this is a clock input event (has current_time and countdown)
      if (data.current_time && data.countdown && data.instance_id) {
        console.log('Clock event received:', data, 'Instance mapping:', instanceIdMapping);
        // Find which interaction this matches by instance_id
        const interactionIndex = instanceIdMapping[data.instance_id];
        if (interactionIndex !== undefined) {
          setClockTimes(prev => {
            const newTimes = {
              ...prev,
              [interactionIndex]: {
                current_time: data.current_time,
                countdown: data.countdown
              }
            };
            return newTimes;
          });
        }
      }
    };
    
    addMessageHandler(messageHandler);
    
    return () => {
      removeMessageHandler(messageHandler);
    };
  }, [instanceIdMapping]);

  // Update instance_id mapping when interactions change
  useEffect(() => {
    // Clear old mappings and rebuild
    setInstanceIdMapping({});
    setClockTimes({});

    let retryCount = 0;
    const maxRetries = 5;
    const retryDelay = 1000; // ms

    const updateInstanceMapping = async () => {
      try {
        const instancesData = await fetchModuleInstances();
        const newMapping: Record<string, number> = {};
        // Build mapping from instance_id to interaction index
        instancesData.instances.forEach((instance: any) => {
          interactions.forEach((interaction, idx) => {
            if (
              interaction.input.module === instance.module_id &&
              JSON.stringify(interaction.input.config) === JSON.stringify(instance.config)
            ) {
              newMapping[instance.instance_id] = idx;
            }
          });
        });
        setInstanceIdMapping(newMapping);
        // If mapping is empty and we haven't hit max retries, try again after delay
        if (Object.keys(newMapping).length === 0 && retryCount < maxRetries) {
          retryCount++;
          setTimeout(updateInstanceMapping, retryDelay);
        }
      } catch (error) {
        console.error('Failed to fetch module instances:', error);
        // Optionally retry on error as well
        if (retryCount < maxRetries) {
          retryCount++;
          setTimeout(updateInstanceMapping, retryDelay);
        }
      }
    };

    if (interactions.length > 0) {
      updateInstanceMapping();
    }
    // No cleanup needed for retry timeouts since they are short-lived
  }, [interactions]);

  // Function to refresh instance mapping after module restarts
  const refreshInstanceMapping = async () => {
    // Small delay to allow modules to restart
    setTimeout(async () => {
      try {
        const instancesData = await fetchModuleInstances();
        const newMapping: Record<string, number> = {};
        
        // Build mapping from instance_id to interaction index
        instancesData.instances.forEach((instance: any) => {
          // Match instance to interaction by module type and config
          interactions.forEach((interaction, idx) => {
            if (interaction.input.module === instance.module_id && 
                JSON.stringify(interaction.input.config) === JSON.stringify(instance.config)) {
              newMapping[instance.instance_id] = idx;
            }
          });
        });
        
        setInstanceIdMapping(newMapping);
      } catch (error) {
        console.error('Failed to refresh module instances:', error);
      }
    }, 500); // 500ms delay
  };

  // Helper to update a field in an interaction
  const updateInteraction = (idx: number, io: 'input' | 'output', key: string, value: any) => {
    setInteractions(prev => prev.map((int, i) =>
      i === idx ? {
        ...int,
        [io]: {
          ...int[io],
          config: {
            ...int[io].config,
            [key]: value
          }
        }
      } : int
    ));
    setDirtyStates(prev => ({
      ...prev,
      [idx]: {
        ...prev[idx],
        [io]: true
      }
    }));
  };

  // Helper to change module
  const changeModule = (idx: number, io: 'input' | 'output', moduleId: string) => {
    setInteractions(prev => prev.map((int, i) => {
      if (i !== idx) return int;
      // Try to restore config for the selected module from originalInteractions
      let restoredConfig = {};
      if (originalInteractions[idx] && originalInteractions[idx][io].module === moduleId) {
        restoredConfig = originalInteractions[idx][io].config || {};
      }
      return {
        ...int,
        [io]: {
          module: moduleId,
          config: restoredConfig
        }
      };
    }));
    setDirtyStates(prev => ({
      ...prev,
      [idx]: {
        ...prev[idx],
        [io]: true
      }
    }));
  };

  // Add new interaction
  const addInteraction = () => {
    setInteractions(prev => ([
      ...prev,
      {
        input: { module: modules[0]?.id || '', config: {} },
        output: { module: modules[0]?.id || '', config: {} }
      }
    ]));
  };

  // Remove interaction
  const removeInteraction = async (idx: number) => {
    setDeleting(idx);
    setError(null);
    // Determine if this interaction exists in the backend (i.e., was loaded from backend)
    // We'll assume interactions loaded from backend are those present at initial load
    // and new ones are appended to the end
    const isUnsaved = idx >= (await fetchConfig()).interactions.length;
    if (isUnsaved) {
      // Just remove from local state, no backend call
      setInteractions(prev => prev.filter((_, i) => i !== idx));
      setClockTimes(prev => {
        const newTimes = { ...prev };
        delete newTimes[idx];
        // Shift down all indices after the deleted one
        const shiftedTimes: Record<number, { current_time: string; countdown: string }> = {};
        Object.keys(newTimes).forEach(key => {
          const oldIdx = parseInt(key);
          if (oldIdx > idx) {
            shiftedTimes[oldIdx - 1] = newTimes[oldIdx];
          } else {
            shiftedTimes[oldIdx] = newTimes[oldIdx];
          }
        });
        return shiftedTimes;
      });
      setDeleting(null);
      return;
    }
    try {
      await deleteInteraction(idx);
      // Remove from local state
      setInteractions(prev => prev.filter((_, i) => i !== idx));
      // Update clock times to remove the deleted interaction
      setClockTimes(prev => {
        const newTimes = { ...prev };
        delete newTimes[idx];
        // Shift down all indices after the deleted one
        const shiftedTimes: Record<number, { current_time: string; countdown: string }> = {};
        Object.keys(newTimes).forEach(key => {
          const oldIdx = parseInt(key);
          if (oldIdx > idx) {
            shiftedTimes[oldIdx - 1] = newTimes[oldIdx];
          } else {
            shiftedTimes[oldIdx] = newTimes[oldIdx];
          }
        });
        return shiftedTimes;
      });
      // Refresh instance mapping after modules restart
      await refreshInstanceMapping();
    } catch (e: any) {
      setError(e.response?.data?.error || e.message || 'Failed to delete interaction');
    } finally {
      setDeleting(null);
    }
  };

  // Save interactions
  const saveInteractions = async () => {
    setSaving(true);
    setSaveSuccess(false);
    setError(null);
    try {
      await updateConfig({ installation_name: '', interactions });
      setSaveSuccess(true);
      setOriginalInteractions(interactions); // <-- update originalInteractions
      // Clear all dirty states
      setDirtyStates({});
      // Refresh instance mapping after modules restart
      await refreshInstanceMapping();
    } catch (e: any) {
      setError(e.message || 'Failed to save');
    } finally {
      setSaving(false);
      setTimeout(() => setSaveSuccess(false), 2000);
    }
  };

  // Render config fields for a module
  const renderFields = (fields: ModuleManifestField[] = [], config: Record<string, any>, idx: number, io: 'input' | 'output', interaction: Interaction) => {
    // Custom layout for audio_output output module
    if (io === 'output' && interaction.output.module === 'audio_output') {
      // Find fields
      const fileField = fields.find(f => f.name === 'file_path');
      const waveformField = fields.find(f => f.name === 'waveform');
      const volumeField = fields.find(f => f.name === 'volume');
      return (
        <Box>
          {/* Row 2: File select/upload and Play button */}
          <Grid container spacing={2} alignItems="stretch">
            {/* Left: Select File + Upload */}
            <Grid item xs={7}>
              {fileField && (
                <Box>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    {fileField.label || fileField.name}
                  </Typography>
                  <FileSelector
                    value={config[fileField.name] ?? ''}
                    onChange={(value) => {
                      updateInteraction(idx, io, fileField.name, value);
                    }}
                    directory="modules/audio_output/assets/audio"
                  />
                  {/* Upload button (reuse FileSelector's upload or add a separate button if needed) */}
                </Box>
              )}
            </Grid>
            {/* Right: Play button (large square) */}
            <Grid item xs={5}>
              <Box display="flex" alignItems="center" justifyContent="center" height={120}>
                <span style={{ display: 'inline-block', width: 96, height: 96 }}>
                  <Button
                    variant="contained"
                    color="primary"
                    size="large"
                    disabled={!!dirtyStates[idx]?.output}
                    onClick={async () => {
                      try {
                        await axios.post('http://localhost:8000/api/play_audio', { interaction_index: idx });
                      } catch (e: any) {
                        let msg = 'Failed to play output';
                        if (e.response && e.response.data && e.response.data.error) {
                          msg += `: ${e.response.data.error}`;
                        }
                        alert(msg);
                      }
                    }}
                    style={{
                      width: 96,
                      height: 96,
                      fontSize: 24,
                      opacity: dirtyStates[idx]?.output ? 0.5 : 1,
                      pointerEvents: dirtyStates[idx]?.output ? 'none' : 'auto',
                      cursor: dirtyStates[idx]?.output ? 'not-allowed' : 'pointer',
                      borderRadius: 16
                    }}
                    title={dirtyStates[idx]?.output ? 'Save changes to enable Play' : 'Trigger audio playback'}
                  >
                    ▶
                  </Button>
                </span>
              </Box>
            </Grid>
          </Grid>
          {/* Row 3: Waveform */}
          {waveformField && (
            <Box mt={2} sx={{ width: 400 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                {waveformField.label || waveformField.name}
              </Typography>
              {(() => {
                const filePath = config.file_path || '';
                const fileName = filePath.split('/').pop() || filePath.split('\\').pop() || '';
                const waveformPath = fileName ? `/modules/audio_output/assets/images/${fileName}.waveform.png` : null;
                return (
                  <Box sx={{ width: 400, height: 100, border:1, borderRadius: 1, display: 'flex', alignItems: 'center', justifyContent: 'flex-start', backgroundColor: '#f5f5f5' }}>
                    {waveformPath ? (
                      <img 
                        src={waveformPath} 
                        alt="Waveform" 
                        style={{ width: 400, height: 100, objectFit: 'contain', display: 'block' }}
                        onError={(e) => {
                          e.currentTarget.style.display = 'none';
                          const nextElement = e.currentTarget.nextElementSibling as HTMLElement;
                          if (nextElement) {
                            nextElement.style.display = 'block';
                          }
                        }}
                        onLoad={(e) => {
                          const errorElement = e.currentTarget.nextElementSibling as HTMLElement;
                          if (errorElement) {
                            errorElement.style.display = 'none';
                          }
                        }}
                      />
                    ) : null}
                    <Typography 
                      variant="caption" 
                      color="text.secondary"
                      style={{ display: waveformPath ? 'none' : 'block' }}
                    >
                      {fileName ? 'No waveform available' : 'Select audio file first'}
                    </Typography>
                  </Box>
                );
              })()}
            </Box>
          )}
          {/* Row 4: Volume */}
          {volumeField && (
            <Box mt={2}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                {volumeField.label || volumeField.name}
              </Typography>
              <Slider
                value={config[volumeField.name] ?? volumeField.default ?? 100}
                onChange={(_, value) => updateInteraction(idx, io, volumeField.name, value as number)}
                min={volumeField.min || 0}
                max={volumeField.max || 100}
                valueLabelDisplay="auto"
                size="small"
              />
              <Typography variant="caption" color="text.secondary" align="center" display="block">
                {config[volumeField.name] ?? volumeField.default ?? 100}
              </Typography>
            </Box>
          )}
        </Box>
      );
    }
    // Fallback to generic layout for other modules
    return (
      <Grid container spacing={2} columns={12}>
        {(fields || []).filter(field => field.type !== 'label').map(field => {
          // Handle different field types
          if (field.type === 'slider') {
            return (
              <Grid key={field.name} sx={{ gridColumn: 'span 4' }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  {field.label || field.name}
                </Typography>
                <Box sx={{ px: 2 }}>
                  <Slider
                    value={config[field.name] ?? field.default ?? 0}
                    onChange={(_, value) => updateInteraction(idx, io, field.name, value)}
                    min={field.min || 0}
                    max={field.max || 100}
                    valueLabelDisplay="auto"
                    size="small"
                  />
                </Box>
                <Typography variant="caption" color="text.secondary" align="center" display="block">
                  {config[field.name] ?? field.default ?? 0}
                </Typography>
              </Grid>
            );
          }
          
          if (field.type === 'waveform') {
            // Get the file path to determine waveform image path
            const filePath = config.file_path || '';
            const fileName = filePath.split('/').pop() || filePath.split('\\').pop() || '';
            const waveformPath = fileName ? `/modules/audio_output/assets/images/${fileName}.waveform.png` : null;
            
            return (
              <Grid key={`${field.name}-${filePath}`} sx={{ gridColumn: 'span 4' }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  {field.label || field.name}
                </Typography>
                <Box sx={{ 
                  width: '100%', 
                  height: 100, 
                  border:1, 
                  borderRadius: 1,
                  display: 'flex',        alignItems: 'center',    justifyContent: 'center',   backgroundColor: '#f5f5f5'
                }}>
                  {waveformPath ? (
                    <img 
                      src={waveformPath} 
                      alt="Waveform" 
                      style={{ 
                        maxWidth: '100%', 
                        maxHeight: '100%', 
                        objectFit: 'contain' 
                      }}
                      onError={(e) => {
                        e.currentTarget.style.display = 'none';
                        const nextElement = e.currentTarget.nextElementSibling as HTMLElement;
                        if (nextElement) {
                          nextElement.style.display = 'block';
                        }
                      }}
                      onLoad={(e) => {
                        // Hide error message when image loads successfully
                        const errorElement = e.currentTarget.nextElementSibling as HTMLElement;
                        if (errorElement) {
                          errorElement.style.display = 'none';
                        }
                      }}
                    />
                  ) : null}
                  <Typography 
                    variant="caption" 
                    color="text.secondary"
                    style={{ display: waveformPath ? 'none' : 'block' }}
                  >
                    {fileName ? 'No waveform available' : 'Select audio file first'}                </Typography>
                </Box>
              </Grid>
            );
          }
          
          if (field.type === 'filepath') {
            return (
              <Grid key={field.name} sx={{ gridColumn: 'span 4' }}>
                <Box display="flex" alignItems="center" gap={2}>
                  <FileSelector
                    value={config[field.name] ?? ''}
                    onChange={(value) => {
                      updateInteraction(idx, io, field.name, value);
                      // Do not call saveInteractions here; let Save/Apply handle it
                    }}
                    directory="modules/audio_output/assets/audio"
                  />
                  {/* Play button for output modules, generic logic */}
                  {io === 'output' && manifests[interaction.output.module]?.supports_manual_trigger && (
                    <span style={{ display: 'inline-block' }}>
                      <Button
                        variant="outlined"
                        size="small"
                        disabled={!!dirtyStates[idx]?.output}
                        onClick={async () => {
                          try {
                            const playEndpoints: Record<string, string> = {
                              'audio_output': 'play_audio',
                              'osc_output': 'play_osc',
                              'dmx_output': 'play_dmx',
                            };
                            const moduleId = interaction.output.module;
                            const endpoint = playEndpoints[moduleId] || 'play_audio';
                            await axios.post(`http://localhost:8000/api/${endpoint}`, { interaction_index: idx });
                          } catch (e: any) {
                            let msg = 'Failed to play output';
                            if (e.response && e.response.data && e.response.data.error) {
                              msg += `: ${e.response.data.error}`;
                            }
                            alert(msg);
                          }
                        }}
                        style={dirtyStates[idx]?.output ? { opacity: 0.5, pointerEvents: 'none', cursor: 'not-allowed' } : {}}
                        title={dirtyStates[idx]?.output ? 'Save changes to enable Play' : 'Trigger output'}
                      >
                        Play
                      </Button>
                    </span>
                  )}
                </Box>
              </Grid>
            );
          }
          
          // Default text field
          return (
            <Grid key={field.name} sx={{ gridColumn: 'span 4' }}>
              <TextField
                label={field.label || field.name}
                value={config[field.name] ?? field.default ?? ''}          onChange={e => updateInteraction(idx, io, field.name, e.target.value)}
                fullWidth
                size="small"
                helperText={field.description}
              />
            </Grid>
          );
        })}
      </Grid>
    );
  };

  if (loading) return <Box p={4}><CircularProgress /></Box>;
  if (error) return <Box p={4}><Alert severity="error">{error}</Alert></Box>;

  return (
    <Box p={4}>
      <Typography variant="h4" gutterBottom>Interaction Editor</Typography>
      <Box display="flex" alignItems="center" mb={2}>
        <Button variant="contained" startIcon={<AddIcon />} onClick={addInteraction} sx={{ mr: 2 }}>Add Interaction</Button>
        <Button
          variant="contained"
          color="primary"
          onClick={saveInteractions}
          disabled={saving}
          startIcon={<SaveIcon />}
        >
          Save / Apply
        </Button>
        {saveSuccess && <Typography color="success.main" sx={{ ml: 2, display: 'inline' }}>Saved!</Typography>}
      </Box>
      {interactions.length === 0 && <Alert severity="info">No interactions defined.</Alert>}
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {interactions.map((interaction, idx) => (
        <Paper key={idx} sx={{ mb: 3, p: 2, width: '70vw', maxWidth: 900, margin: '0 auto' }} elevation={2}>
          <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
            <Typography variant="h6">Interaction {idx + 1}</Typography>
            <IconButton 
              onClick={() => removeInteraction(idx)} 
              color="error"
              disabled={deleting === idx}
            >
              {deleting === idx ? <CircularProgress size={20} /> : <DeleteIcon />}
            </IconButton>
          </Box>
          <Grid container spacing={2} columns={12} display="flex" flexDirection="row" gap={2}>
            {/* Input Module (left) */}
            <Grid sx={{ flex: 1, minWidth: 0 }}>
              <Typography variant="subtitle1">Input</Typography>
              <Select
                value={interaction.input.module}
                onChange={e => changeModule(idx, 'input', e.target.value)}
                fullWidth
                size="small"
                sx={{ mb: 1 }}
              >
                {modules.filter(m => m.type === 'input').map(m => (
                  <MenuItem key={m.id} value={m.id}>{m.name || m.id}</MenuItem>
                ))}
              </Select>
              {(() => {
                const manifest = manifests[interaction.input.module];
                if (Array.isArray(manifest?.fields) && manifest.fields.length > 0) {
                  return renderFields(manifest.fields, interaction.input.config, idx, 'input', interaction);
                } else {
                  return <div>No fields found for this module</div>;
                }
              })()}
              {interaction.input.module === 'time_input_trigger' && clockTimes[idx] && (
                <Box sx={{ mt: 1 }}>
                  <Typography variant="body2" color="text.secondary">
                    Current: {clockTimes[idx].current_time || '--:--:--'} | 
                    Countdown: {clockTimes[idx].countdown || '--:--:--'}
                  </Typography>
                </Box>
              )}
            </Grid>
            {/* Output Module (right) */}
            <Grid sx={{ flex: 1, minWidth: 0 }}>
              <Typography variant="subtitle1">Output</Typography>
              <Select
                value={interaction.output.module}
                onChange={e => changeModule(idx, 'output', e.target.value)}
                fullWidth
                size="small"
                sx={{ mb: 1 }}
              >
                {modules.filter(m => m.type === 'output').map(m => (
                  <MenuItem key={m.id} value={m.id}>{m.name || m.id}</MenuItem>
                ))}
              </Select>
              {(() => {
                const manifest = manifests[interaction.output.module];
                if (Array.isArray(manifest?.fields) && manifest.fields.length > 0) {
                  return renderFields(manifest.fields, interaction.output.config, idx, 'output', interaction);
                } else {
                  return <div>No fields found for this module</div>;
                }
              })()}
            </Grid>
          </Grid>
        </Paper>
      ))}
    </Box>
  );
};

export default InteractionEditor; 