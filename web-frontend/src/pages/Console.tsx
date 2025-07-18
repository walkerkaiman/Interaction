import React, { useEffect, useState } from 'react';
import { Box, Typography, Paper, FormControl, InputLabel, Select, MenuItem } from '@mui/material';
import { connectWebSocket, addMessageHandler, removeMessageHandler } from '../api/ws';

const LOG_CATEGORIES = [
  { value: 'all', label: 'All Logs' },
  { value: 'system', label: 'System' },
  { value: 'audio', label: 'Audio' },
  { value: 'osc', label: 'OSC' },
  { value: 'serial', label: 'Serial' },
  { value: 'dmx', label: 'DMX/Art-Net/sACN' },
];

interface LogEntry {
  message: string;
  module: string;
  timestamp: string;
  category: string;  // Added category field
}

const Console: React.FC = () => {
  connectWebSocket(); // Ensure WebSocket is connected
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [category, setCategory] = useState('all');

  useEffect(() => {
    const handler = (data: any) => {
      console.log('[WS DEBUG] Received message:', JSON.stringify(data, null, 2)); // Print full message
      if (data.type === 'console_log') {
        setLogs(prev => {
          const newLogs = [...prev, {
            message: data.message,
            module: data.module || 'Unknown',
            timestamp: data.timestamp || new Date().toLocaleTimeString(),
            category: data.category || 'system'  // Default to system if no category
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
          {LOG_CATEGORIES.map(cat => (
            <MenuItem key={cat.value} value={cat.value}>{cat.label}</MenuItem>
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
              <span style={{ color: '#4CAF50', marginLeft: 8 }}>[{log.module}]</span>
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