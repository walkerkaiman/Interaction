import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { AppBar, Toolbar, Typography, Drawer, List, ListItem, ListItemText, Box, CssBaseline } from '@mui/material';
import Dashboard from './pages/Dashboard';
import Modules from './pages/Modules';
import Events from './pages/Events';
import InteractionEditor from './pages/InteractionEditor';
import Performance from './pages/Performance';

const drawerWidth = 220;

const navItems = [
  { text: 'Dashboard', path: '/' },
  { text: 'Modules', path: '/modules' },
  { text: 'Events', path: '/events' },
  { text: 'Interaction Editor', path: '/editor' },
  { text: 'Performance', path: '/performance' },
];

const App: React.FC = () => {
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
            <Route path="/" element={<Dashboard />} />
            <Route path="/modules" element={<Modules />} />
            <Route path="/events" element={<Events />} />
            <Route path="/editor" element={<InteractionEditor />} />
            <Route path="/performance" element={<Performance />} />
          </Routes>
        </Box>
      </Box>
    </Router>
  );
};

export default App;
