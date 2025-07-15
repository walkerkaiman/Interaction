import React from 'react';
import { Box, Typography } from '@mui/material';

const InteractionEditor: React.FC = () => {
  return (
    <Box p={4}>
      <Typography variant="h4" gutterBottom>
        Interaction Editor
      </Typography>
      <Typography variant="body1">
        Here you will be able to visually connect modules and design interactions (drag-and-drop coming soon).
      </Typography>
    </Box>
  );
};

export default InteractionEditor; 