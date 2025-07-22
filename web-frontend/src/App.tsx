import { useState } from 'react';
import { CssBaseline, Box, Drawer, List, ListItem, ListItemButton, ListItemText, ThemeProvider, createTheme } from '@mui/material';
import WikiPage from './pages/Wiki';
import Console from './pages/Console';
import Performance from './pages/Performance';

const drawerWidth = 220;
const pages = [
  { label: 'Module Wiki', key: 'wiki' },
  { label: 'Interactions', key: 'interactions' },
  { label: 'Console', key: 'console' },
  { label: 'Performance', key: 'performance' },
];

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
  },
});

const InteractionsPage = () => <div><h2>Interactions</h2><p>Interactions page placeholder.</p></div>;

const App = () => {
  const [selected, setSelected] = useState('wiki');

  let content = null;
  switch (selected) {
    case 'wiki':
      content = <WikiPage />;
      break;
    case 'interactions':
      content = <InteractionsPage />;
      break;
    case 'console':
      content = <Console />;
      break;
    case 'performance':
      content = <Performance />;
      break;
    default:
      content = null;
  }

  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <Box sx={{ display: 'flex', height: '100vh' }}>
        <Drawer
          variant="permanent"
          sx={{
            width: drawerWidth,
            flexShrink: 0,
            [`& .MuiDrawer-paper`]: { width: drawerWidth, boxSizing: 'border-box' },
          }}
        >
          <List>
            {pages.map((page) => (
              <ListItem key={page.key} disablePadding>
                <ListItemButton selected={selected === page.key} onClick={() => setSelected(page.key)}>
                  <ListItemText primary={page.label} />
                </ListItemButton>
              </ListItem>
            ))}
          </List>
        </Drawer>
        <Box component="main" sx={{ flexGrow: 1, p: 3, overflow: 'auto' }}>
          {content}
        </Box>
      </Box>
    </ThemeProvider>
  );
};

export default App;
