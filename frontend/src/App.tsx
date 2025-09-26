import React, { useState, useContext } from 'react';
import { Box, IconButton, Typography, Paper, Grid, Fade } from '@mui/material';
import { Brightness4, Brightness7, Web, DataUsage, ModelTraining, Policy } from '@mui/icons-material';
import Layout from './components/Layout';
import { ThemeContext } from './theme/ThemeContext';
import Scraping from './components/Scraping';
import DataManagement from './components/DataManagement';
import ModelTraining from './components/ModelTraining';
import Evaluation from './components/Evaluation';

const Dashboard = () => (
    <Fade in={true} timeout={1000}>
        <Paper elevation={4} sx={{ p: 4, textAlign: 'center', background: 'rgba(255,255,255,0.05)' }}>
            <Typography variant="h2" component="h1" gutterBottom sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                ESP32 AI Toolkit
            </Typography>
            <Typography variant="h6" color="text.secondary" paragraph>
                Your all-in-one solution for building, training, and evaluating TinyML models for ESP32.
            </Typography>
            <Grid container spacing={4} sx={{ mt: 4 }}>
                {[
                    { icon: <Web fontSize="large"/>, title: 'Scrape Data' },
                    { icon: <DataUsage fontSize="large"/>, title: 'Manage & Process' },
                    { icon: <ModelTraining fontSize="large"/>, title: 'Fine-Tune Models' },
                    { icon: <Policy fontSize="large"/>, title: 'Evaluate Performance' },
                ].map(item => (
                    <Grid item xs={12} sm={6} md={3} key={item.title}>
                        <Box>
                            {item.icon}
                            <Typography variant="subtitle1" sx={{ mt: 1 }}>{item.title}</Typography>
                        </Box>
                    </Grid>
                ))}
            </Grid>
        </Paper>
    </Fade>
);


function App() {
  const { mode, toggleTheme } = useContext(ThemeContext);
  const [activeView, setActiveView] = useState('Dashboard');

  const renderActiveView = () => {
    switch (activeView) {
      case 'Web Scraping':
        return <Scraping />;
      case 'Data Management':
        return <DataManagement />;
      case 'Model Training':
        return <ModelTraining />;
      case 'Evaluation':
        return <Evaluation />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <Layout setActiveView={setActiveView}>
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', mb: 2 }}>
            <IconButton sx={{ ml: 1 }} onClick={toggleTheme} color="inherit">
                {mode === 'dark' ? <Brightness7 /> : <Brightness4 />}
            </IconButton>
        </Box>
        {renderActiveView()}
    </Layout>
  );
}

export default App;
