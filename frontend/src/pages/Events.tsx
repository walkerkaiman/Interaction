import React from 'react';
import { Box, Typography } from '@mui/material';

const Events: React.FC = () => {
  return (
    <Box p={4}>
      <Typography variant="h4" gutterBottom>
        Real-Time Events
      </Typography>
      <Typography variant="body1">
        This page will display a real-time log of system events, triggers, and messages.
      </Typography>
    </Box>
  );
};

export default Events; 