import React from 'react';
import { Box, Typography } from '@mui/material';

const Performance: React.FC = () => {
  return (
    <Box p={4}>
      <Typography variant="h4" gutterBottom>
        Performance Monitoring
      </Typography>
      <Typography variant="body1">
        This page will show real-time system performance stats (CPU, memory, event latency, etc.).
      </Typography>
    </Box>
  );
};

export default Performance; 