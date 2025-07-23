import { useState, useEffect } from 'react';
import { Box, Button, Typography, Paper, Select, MenuItem, FormControl, InputLabel, Snackbar, Alert, Divider } from '@mui/material';
import ModuleSettingsForm from '../components/ModuleSettingsForm';
import { useModulesStore } from '../state/useModulesStore';

const INTERACTION_DRAFT_KEY = 'interactionDraft';

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
      <Typography variant="h5" gutterBottom>Existing Interactions</Typography>
      {interactions.length === 0 ? (
        <Typography color="text.secondary">No interactions registered.</Typography>
      ) : (
        interactions.map((interaction, idx) => (
          <Paper key={idx} sx={{ p: 2, mb: 2 }}>
            <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, gap: 3 }}>
              <Box sx={{ flex: 1 }}>
                <Typography variant="subtitle1">Input: {interaction.input.module}</Typography>
                <pre style={{ fontSize: 13, background: '#222', color: '#fff', padding: 8, borderRadius: 4 }}>{JSON.stringify(interaction.input.config, null, 2)}</pre>
              </Box>
              <Box sx={{ flex: 1 }}>
                <Typography variant="subtitle1">Output: {interaction.output.module}</Typography>
                <pre style={{ fontSize: 13, background: '#222', color: '#fff', padding: 8, borderRadius: 4 }}>{JSON.stringify(interaction.output.config, null, 2)}</pre>
              </Box>
            </Box>
          </Paper>
        ))
      )}
    </Box>
  );
};

export default Interactions; 