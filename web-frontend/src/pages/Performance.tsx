import React, { useEffect, useState, useRef } from 'react';
import { Box, Typography, Card, CardContent, LinearProgress } from '@mui/material';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend, CartesianGrid } from 'recharts';
import { connectWebSocket, addMessageHandler, removeMessageHandler } from '../api/ws';

interface StatPoint {
  time: string;
  cpu: number;
  temperature: number | null;
}

interface SystemInfo {
  cpu?: { manufacturer?: string; brand?: string; speed?: string; cores?: number };
  mem?: { total?: number };
  osInfo?: { platform?: string; distro?: string; release?: string };
  [key: string]: any;
}

const MAX_POINTS = 60;

const Performance: React.FC = () => {
  const [stats, setStats] = useState<StatPoint[]>([]);
  const [memory, setMemory] = useState(0);
  const [systemInfo, setSystemInfo] = useState<SystemInfo>({});
  const [uptime, setUptime] = useState(0);
  const [load, setLoad] = useState<number[]>([]);
  const wsConnected = useRef(false);

  useEffect(() => {
    connectWebSocket();
    const handler = (data: any) => {
      if (data.type === 'system_stats') {
        setStats(prev => {
          const now = new Date();
          const time = now.toLocaleTimeString();
          const next = [
            ...prev,
            {
              time,
              cpu: Math.round((data.cpu || 0) * 100),
              temperature: data.temperature !== null ? data.temperature : null,
            },
          ];
          return next.length > MAX_POINTS ? next.slice(-MAX_POINTS) : next;
        });
        setMemory(Math.round((data.memory || 0) * 100));
        setUptime(data.uptime || 0);
        setLoad(data.load || []);
      }
    };
    addMessageHandler(handler);
    wsConnected.current = true;
    return () => {
      removeMessageHandler(handler);
      wsConnected.current = false;
    };
  }, []);

  useEffect(() => {
    fetch('/api/system_info')
      .then(res => res.json())
      .then(setSystemInfo);
  }, []);

  const formatUptime = (seconds: number) => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    return `${h}h ${m}m ${s}s`;
  };

  return (
    <Box p={2}>
      <Typography variant="h4" gutterBottom>Performance Monitoring</Typography>
      <Box display="flex" flexDirection={{ xs: 'column', md: 'row' }} gap={2}>
        <Box flex={2}>
          <Card sx={{ mb: 2 }}>
            <CardContent>
              <Typography variant="h6">CPU Usage (last 60s)</Typography>
              <ResponsiveContainer width="100%" height={180}>
                <LineChart data={stats} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                  <XAxis dataKey="time" minTickGap={15} />
                  <YAxis domain={[0, 100]} tickFormatter={v => `${v}%`} />
                  <Tooltip formatter={v => `${v}%`} />
                  <Legend />
                  <CartesianGrid strokeDasharray="3 3" />
                  <Line type="monotone" dataKey="cpu" stroke="#4caf50" dot={false} name="CPU %" />
                  {stats.some(s => s.temperature !== null) && (
                    <Line type="monotone" dataKey="temperature" stroke="#ff9800" dot={false} name="Temp (°C)" yAxisId={1} />
                  )}
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Box>
        <Box flex={1}>
          <Card sx={{ mb: 2 }}>
            <CardContent>
              <Typography variant="h6">Memory Usage</Typography>
              <Box display="flex" alignItems="center" gap={2}>
                <Box flex={1}>
                  <LinearProgress variant="determinate" value={memory} sx={{ height: 16, borderRadius: 8 }} />
                </Box>
                <Typography>{memory}%</Typography>
              </Box>
            </CardContent>
          </Card>
          <Card>
            <CardContent>
              <Typography variant="h6">System Info</Typography>
              <Typography variant="body2">CPU: {systemInfo.cpu?.brand} ({systemInfo.cpu?.cores} cores @ {systemInfo.cpu?.speed} GHz)</Typography>
              <Typography variant="body2">OS: {systemInfo.osInfo?.distro} {systemInfo.osInfo?.release}</Typography>
              <Typography variant="body2">Total Memory: {systemInfo.mem?.total ? (systemInfo.mem.total / (1024 ** 3)).toFixed(1) : '?'} GB</Typography>
              <Typography variant="body2">Uptime: {formatUptime(uptime)}</Typography>
              <Typography variant="body2">Load Avg: {load.map(l => l.toFixed(2)).join(' / ')}</Typography>
            </CardContent>
          </Card>
        </Box>
      </Box>
    </Box>
  );
};

export default Performance; 