import React, { useEffect, useState } from 'react';
import { Box, Typography, Paper, FormControl, InputLabel, Select, MenuItem } from '@mui/material';
import { connectWebSocket, addMessageHandler, removeMessageHandler } from '../api/ws';

interface LogEntry {
  message: string;
  module?: string;
  timestamp: string;
  category: string;
}

const Console: React.FC = () => {
  connectWebSocket(); // Ensure WebSocket is connected
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [category, setCategory] = useState('all');
  const [logLevels, setLogLevels] = useState<string[]>([]);

  useEffect(() => {
    // Fetch log levels from backend
    fetch('/api/log_levels')
      .then(res => res.json())
      .then(levels => setLogLevels(levels))
      .catch(() => setLogLevels([]));
  }, []);

  useEffect(() => {
    const handler = (data: any) => {
      if (data.type === 'log') {
        setLogs(prev => {
          const newLogs = [...prev, {
            message: data.message,
            module: data.module || '',
            timestamp: data.timestamp || new Date().toLocaleTimeString(),
            category: data.level || 'System',
          }];
          return newLogs;
        });
      }
    };
    addMessageHandler(handler);
    return () => removeMessageHandler(handler);
  }, []);

  // Filter logs by category
  const filteredLogs = category === 'all'
    ? logs
    : logs.filter(log => log.category === category);

  return (
    <Box p={2}>
      <Typography variant="h5" gutterBottom>Console</Typography>
      <FormControl size="small" sx={{ mb: 2, minWidth: 180 }}>
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
      <Paper sx={{ maxHeight: 400, overflow: 'auto', p: 2, background: '#111', color: '#0f0', fontFamily: 'monospace' }}>
        {filteredLogs.length === 0 ? (
          <Typography color="text.secondary">No logs yet...</Typography>
        ) : (
          filteredLogs.map((log, idx) => (
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