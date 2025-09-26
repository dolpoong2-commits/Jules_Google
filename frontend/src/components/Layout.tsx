import React, { ReactNode } from 'react';
import { Box, CssBaseline, AppBar, Toolbar, Typography, Drawer, List, ListItem, ListItemButton, ListItemIcon, ListItemText } from '@mui/material';
import { Web, DataUsage, ModelTraining, Policy, Home } from '@mui/icons-material';
import LogPanel from './LogPanel';

const drawerWidth = 240;

interface LayoutProps {
  children: ReactNode;
  setActiveView: (view: string) => void;
}

const Layout = ({ children, setActiveView }: LayoutProps) => {
  const menuItems = [
    { text: 'Dashboard', icon: <Home /> },
    { text: 'Web Scraping', icon: <Web /> },
    { text: 'Data Management', icon: <DataUsage /> },
    { text: 'Model Training', icon: <ModelTraining /> },
    { text: 'Evaluation', icon: <Policy /> },
  ];

  return (
    <Box sx={{ display: 'flex' }}>
      <CssBaseline />
      <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
        <Toolbar>
          <Typography variant="h6" noWrap component="div">
            ESP32 AI Toolkit
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
            {menuItems.map((item) => (
              <ListItem key={item.text} disablePadding>
                <ListItemButton onClick={() => setActiveView(item.text)}>
                  <ListItemIcon>{item.icon}</ListItemIcon>
                  <ListItemText primary={item.text} />
                </ListItemButton>
              </ListItem>
            ))}
          </List>
        </Box>
      </Drawer>
      <Box component="main" sx={{ flexGrow: 1, p: 3, display: 'flex', flexDirection: 'column', height: '100vh' }}>
        <Toolbar />
        <Box sx={{ flexGrow: 1 }}>
            {children}
        </Box>
        <LogPanel />
      </Box>
    </Box>
  );
};

export default Layout;