import React, { useEffect, useState, useRef } from 'react';
import {
  Box, Typography, Paper, Button, Select, MenuItem, TextField, IconButton, CircularProgress, Alert
} from '@mui/material';
import { Grid } from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';
import SaveIcon from '@mui/icons-material/Save';
import { fetchConfig, updateConfig, fetchModules, deleteInteraction, fetchModuleInstances } from '../api/api';
import axios from 'axios';
import { connectWebSocket, addMessageHandler, removeMessageHandler } from '../api/ws';

interface ModuleManifestField {
  name: string;
  type: string;
  default?: any;
  label?: string;
  description?: string;
}

interface ModuleManifest {
  fields: ModuleManifestField[];
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
    const res = await axios.get(`/modules/${moduleId}/manifest.json`);
    return res.data;
  } catch {
    return { fields: [] };
  }
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
  const wsRef = useRef<WebSocket | null>(null);

  // Load modules and interactions
  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const [modulesArr, config] = await Promise.all([
          fetchModules(),
          fetchConfig()
        ]);
        setModules(modulesArr);
        setInteractions(config.interactions || []);
        // Preload manifests for all modules
        const allModuleIds = Array.from(new Set([
          ...modulesArr.map(m => m.id),
          ...((config.interactions || []).flatMap((i: Interaction) => [i.input.module, i.output.module]))
        ]));
        const manifestEntries = await Promise.all(
          allModuleIds.map(async id => [id, await fetchManifest(id)])
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
      console.log('WebSocket received:', data); // Debug log
      // Check if this is a clock input event (has current_time and countdown)
      if (data.current_time && data.countdown && data.instance_id) {
        console.log('Clock event detected:', data); // Debug log
        // Find which interaction this matches by instance_id
        const interactionIndex = instanceIdMapping[data.instance_id];
        console.log('Instance mapping:', instanceIdMapping); // Debug log
        console.log('Found interaction index:', interactionIndex); // Debug log
        if (interactionIndex !== undefined) {
          setClockTimes(prev => {
            const newTimes = {
              ...prev,
              [interactionIndex]: {
                current_time: data.current_time,
                countdown: data.countdown
              }
            };
            console.log('Updated clock times:', newTimes); // Debug log
            return newTimes;
          });
        } else {
          console.log('No interaction found for instance_id:', data.instance_id); // Debug log
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
    
    // Fetch current module instances to build mapping
    const updateInstanceMapping = async () => {
      try {
        console.log('Fetching module instances...'); // Debug log
        const instancesData = await fetchModuleInstances();
        console.log('Module instances data:', instancesData); // Debug log
        const newMapping: Record<string, number> = {};
        
        // Build mapping from instance_id to interaction index
        instancesData.instances.forEach((instance: any) => {
          console.log('Processing instance:', instance); // Debug log
          // Match instance to interaction by module type and config
          interactions.forEach((interaction, idx) => {
            console.log('Checking interaction', idx, ':', interaction); // Debug log
            if (interaction.input.module === instance.module_id && 
                JSON.stringify(interaction.input.config) === JSON.stringify(instance.config)) {
              newMapping[instance.instance_id] = idx;
              console.log('Matched instance', instance.instance_id, 'to interaction', idx); // Debug log
            }
          });
        });
        
        setInstanceIdMapping(newMapping);
        console.log('Updated instance mapping:', newMapping);
      } catch (error) {
        console.error('Failed to fetch module instances:', error);
      }
    };
    
    if (interactions.length > 0) {
      updateInstanceMapping();
    }
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
        console.log('Refreshed instance mapping:', newMapping);
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
  };

  // Helper to change module
  const changeModule = (idx: number, io: 'input' | 'output', moduleId: string) => {
    setInteractions(prev => prev.map((int, i) =>
      i === idx ? {
        ...int,
        [io]: {
          module: moduleId,
          config: {}
        }
      } : int
    ));
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
  const renderFields = (fields: ModuleManifestField[] = [], config: Record<string, any>, idx: number, io: 'input' | 'output') => (
    <Grid container spacing={2} columns={12}>
      {(fields || []).filter(field => field.type !== 'label').map(field => (
        <Grid key={field.name} sx={{ gridColumn: 'span 4' }}>
          <TextField
            label={field.label || field.name}
            value={config[field.name] ?? field.default ?? ''}
            onChange={e => updateInteraction(idx, io, field.name, e.target.value)}
            fullWidth
            size="small"
            helperText={field.description}
          />
        </Grid>
      ))}
    </Grid>
  );

  if (loading) return <Box p={4}><CircularProgress /></Box>;
  if (error) return <Box p={4}><Alert severity="error">{error}</Alert></Box>;

  return (
    <Box p={4}>
      <Typography variant="h4" gutterBottom>Interaction Editor</Typography>
      <Button variant="contained" startIcon={<AddIcon />} onClick={addInteraction} sx={{ mb: 2 }}>Add Interaction</Button>
      {interactions.length === 0 && <Alert severity="info">No interactions defined.</Alert>}
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {interactions.map((interaction, idx) => (
        <Paper key={idx} sx={{ mb: 3, p: 2 }} elevation={2}>
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
                console.log('Input manifest:', manifest);
                console.log('Fields:', manifest?.fields);
                if (Array.isArray(manifest?.fields) && manifest.fields.length > 0) {
                  return renderFields(manifest.fields, interaction.input.config, idx, 'input');
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
                console.log('Output manifest:', manifest);
                console.log('Fields:', manifest?.fields);
                if (Array.isArray(manifest?.fields) && manifest.fields.length > 0) {
                  return renderFields(manifest.fields, interaction.output.config, idx, 'output');
                } else {
                  return <div>No fields found for this module</div>;
                }
              })()}
            </Grid>
          </Grid>
        </Paper>
      ))}
      <Box mt={2}>
        <Button
          variant="contained"
          color="primary"
          onClick={saveInteractions}
          disabled={saving}
          sx={{ mt: 2 }}
        >
          Save / Apply
        </Button>
        {saveSuccess && <Typography color="success.main" sx={{ ml: 2, display: 'inline' }}>Saved!</Typography>}
      </Box>
    </Box>
  );
};

export default InteractionEditor; 