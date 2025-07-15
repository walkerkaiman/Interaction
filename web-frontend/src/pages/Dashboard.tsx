import React from 'react';
import { Box, Typography } from '@mui/material';

const Dashboard: React.FC = () => {
  return (
    <Box p={4}>
      <Typography variant="h4" gutterBottom>
        Interactive Art Installation Dashboard
      </Typography>
      <Typography variant="body1">
        Welcome! Use the navigation to manage modules, view real-time events, and edit interactions.
      </Typography>
    </Box>
  );
};

export default Dashboard; 