import React, { useEffect } from 'react';
import { Box, Typography, CircularProgress, Alert, List, ListItem, ListItemText, Paper } from '@mui/material';
import { useModulesStore } from '../state/useModulesStore';

const Modules: React.FC = () => {
  const { modules, loading, error, fetchAll } = useModulesStore();

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  return (
    <Box p={4}>
      <Typography variant="h4" gutterBottom>
        Modules
      </Typography>
      {loading && <CircularProgress />}
      {error && <Alert severity="error">{error}</Alert>}
      {!loading && !error && (
        <Paper elevation={2} sx={{ mt: 2 }}>
          <List>
            {modules.length === 0 && (
              <ListItem>
                <ListItemText primary="No modules found." />
              </ListItem>
            )}
            {modules.map((mod) => (
              <ListItem key={mod.id} divider>
                <ListItemText
                  primary={mod.name || mod.id}
                  secondary={`Type: ${mod.type}`}
                />
              </ListItem>
            ))}
          </List>
        </Paper>
      )}
    </Box>
  );
};

export default Modules; 