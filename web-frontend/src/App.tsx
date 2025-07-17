import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { AppBar, Toolbar, Typography, Drawer, List, ListItem, ListItemText, Box, CssBaseline } from '@mui/material';
import Wiki from './pages/Wiki';
import Events from './pages/Events';
import InteractionEditor from './pages/InteractionEditor';
import Performance from './pages/Performance';
import connectWebSocket from './api/ws';
import ModuleWikiPage from './pages/ModuleWikiPage';

const drawerWidth = 220;

const navItems = [
  { text: 'Wiki', path: '/modules' },
  { text: 'Interactions', path: '/editor' },
  { text: 'Console', path: '/events' },
  { text: 'Performance', path: '/performance' },
];

const App: React.FC = () => {
  useEffect(() => {
    connectWebSocket();
  }, []);

  return (
    <Router>
      <Box sx={{ display: 'flex' }}>
        <CssBaseline />
        <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
          <Toolbar>
            <Typography variant="h6" noWrap component="div">
              Interactive Art Installation
            </Typography>
          </Toolbar>
        </AppBar>
        <Drawer
          variant="permanent"
          sx={{
            width: drawerWidth,
            flexShrink: 0,
            [`& .MuiDrawer-paper`]: { width: drawerWidth, boxSizing: 'border-box' },
          }}
        >
          <Toolbar />
          <Box sx={{ overflow: 'auto' }}>
            <List>
              {navItems.map((item) => (
                <ListItem key={item.text} disablePadding>
                  <Link to={item.path} style={{ textDecoration: 'none', color: 'inherit', width: '100%' }}>
                    <ListItemText primary={item.text} sx={{ pl: 2, py: 1.5 }} />
                  </Link>
                </ListItem>
              ))}
            </List>
          </Box>
        </Drawer>
        <Box component="main" sx={{ flexGrow: 1, bgcolor: 'background.default', p: 3, ml: `${drawerWidth}px` }}>
          <Toolbar />
          <Routes>
            <Route path="/modules" element={<Wiki />} />
            <Route path="/modules/:id" element={<ModuleWikiPage />} />
            <Route path="/editor" element={<InteractionEditor />} />
            <Route path="/events" element={<Events />} />
            <Route path="/performance" element={<Performance />} />
            <Route path="*" element={<Wiki />} />
          </Routes>
        </Box>
      </Box>
    </Router>
  );
};

export default App;
