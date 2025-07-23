import { useState, useEffect } from 'react';
import ModuleSettingsForm from '../components/ModuleSettingsForm';
import { useModulesStore } from '../state/useModulesStore';
import { Box, Typography, Select, MenuItem, FormControl, InputLabel } from '@mui/material';

const InteractionEditor = () => {
  const [selectedModuleName, setSelectedModuleName] = useState('');
  const [selectedModule, setSelectedModule] = useState<any>(null);
  const availableModules: any[] = useModulesStore(state => state.availableModules);
  const modules = useModulesStore(state => state.modules);
  const fetchAvailableModules = useModulesStore(state => state.fetchAvailableModules);

  useEffect(() => {
    fetchAvailableModules();
  }, [fetchAvailableModules]);

  useEffect(() => {
    if (selectedModuleName) {
      const modMeta = availableModules.find((m: any) => m.name === selectedModuleName);
      const modState = modules[selectedModuleName];
      if (modMeta && modState) {
        setSelectedModule({
          id: selectedModuleName,
          manifest: modMeta.manifest,
          config: modState.config,
        });
      } else {
        setSelectedModule(null);
      }
    } else {
      setSelectedModule(null);
    }
  }, [selectedModuleName, availableModules, modules]);

  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h5" gutterBottom>Module Settings</Typography>
      <FormControl sx={{ minWidth: 240, mb: 2 }} size="small">
        <InputLabel id="module-select-label">Select Module</InputLabel>
        <Select
          labelId="module-select-label"
          value={selectedModuleName}
          label="Select Module"
          onChange={e => setSelectedModuleName(e.target.value)}
        >
          <MenuItem value=""><em>None</em></MenuItem>
          {availableModules.map((mod: any) => (
            <MenuItem key={mod.name} value={mod.name}>{mod.manifest?.name || mod.name}</MenuItem>
          ))}
        </Select>
      </FormControl>
      {selectedModule ? (
        <ModuleSettingsForm manifest={selectedModule.manifest} config={selectedModule.config} moduleId={selectedModule.id} />
      ) : (
        <Typography color="text.secondary">Select a module to configure.</Typography>
      )}
    </Box>
  );
};

export default InteractionEditor;
