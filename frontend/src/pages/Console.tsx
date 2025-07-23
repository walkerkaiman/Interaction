import React, { useState } from 'react';
import { Box, Typography, Paper, FormControl, InputLabel, Select, MenuItem, Button } from '@mui/material';
import { useLogStore } from '../state/useLogStore';

const LOG_STORAGE_KEY = 'consoleLogs';

const Console: React.FC = () => {
  const CATEGORY_STORAGE_KEY = 'consoleCategory';
  const [category, setCategory] = useState(() => {
    const stored = localStorage.getItem(CATEGORY_STORAGE_KEY);
    return stored || 'all';
  });
  const [logLevels, setLogLevels] = useState<string[]>([]);
  const getLogsByCategory = useLogStore(state => state.getLogsByCategory);
  const clearLogs = useLogStore(state => state.clearLogs);

  React.useEffect(() => {
    fetch('/api/log_levels')
      .then(res => res.json())
      .then(levels => setLogLevels(levels))
      .catch(() => setLogLevels([]));
  }, []);

  React.useEffect(() => {
    localStorage.setItem(CATEGORY_STORAGE_KEY, category);
  }, [category]);

  // Filter logs by category
  const filteredLogs = getLogsByCategory(category);

  return (
    <Box p={2}>
      <Typography variant="h5" gutterBottom>Console</Typography>
      <Box display="flex" alignItems="center" gap={2} mb={2}>
        <FormControl size="small" sx={{ minWidth: 180 }}>
          <InputLabel id="log-category-label">Log Category</InputLabel>
          <Select
            labelId="log-category-label"
            value={category}
            label="Log Category"
            onChange={e => setCategory(e.target.value)}
          >
            <MenuItem value="all">All Logs</MenuItem>
            {logLevels.map(level => (
              <MenuItem key={level} value={level}>{level}</MenuItem>
            ))}
          </Select>
        </FormControl>
        <Button variant="outlined" color="secondary" size="small" onClick={() => {
          if (category !== 'all') {
            useLogStore.getState().clearCategory(category);
            setCategory('all');
            localStorage.setItem(CATEGORY_STORAGE_KEY, 'all');
          } else {
            clearLogs();
          }
        }}>Reset</Button>
      </Box>
      <Paper sx={{ maxHeight: 400, overflow: 'auto', p: 2, background: '#111', color: '#0f0', fontFamily: 'monospace' }}>
        {filteredLogs.length === 0 ? (
          <Typography color="text.secondary">No logs yet...</Typography>
        ) : (
          filteredLogs.map((log: any, idx: number) => (
            <Box key={idx} sx={{ mb: 1, fontSize: '0.875rem' }}>
              <span style={{ color: '#888' }}>[{log.timestamp}]</span>
              <span style={{ color: '#4CAF50', marginLeft: 8 }}>[{log.module || 'System'}]</span>
              <span style={{ color: '#FF9800', marginLeft: 8 }}>[{log.category.toUpperCase()}]</span>
              <span style={{ marginLeft: 8 }}>{log.message}</span>
            </Box>
          ))
        )}
      </Paper>
    </Box>
  );
};

export default Console; 