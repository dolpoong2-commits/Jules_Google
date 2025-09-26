import React, { useState, useContext } from 'react';
import { Box, Button, TextField, Typography, Paper, CircularProgress } from '@mui/material';
import { LogContext } from '../context/LogContext';

const Scraping = () => {
  const [urls, setUrls] = useState('https://github.com/espressif/esp-idf\nhttps://github.com/espressif/arduino-esp32');
  const [githubRepos, setGithubRepos] = useState('espressif/esp-idf\nespressif/esp-adf');
  const [keywords, setKeywords] = useState('esp32, tinyml');
  const [isLoading, setIsLoading] = useState(false);
  const { addLog } = useContext(LogContext);

  const handleScrape = async () => {
    setIsLoading(true);
    addLog("Scraping process initiated...");

    const urlList = urls.split('\n').filter(url => url.trim() !== '');
    const repoList = githubRepos.split('\n').filter(repo => repo.trim() !== '');
    const keywordList = keywords.split(',').map(kw => kw.trim()).filter(kw => kw !== '');

    try {
      const response = await fetch('http://localhost:8000/scrape/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          urls: urlList,
          github_repos: repoList,
          keywords: keywordList,
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP error! status: ${response.status}, details: ${errorText}`);
      }

      const result = await response.json();
      addLog(`Scraping finished. Status: ${result.status}`, 'SUCCESS');
      result.details.forEach((detail: string) => addLog(`- ${detail}`));
    } catch (error: any) {
      addLog(`Error during scraping: ${error.message}`, 'ERROR');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Paper elevation={3} sx={{ p: 3 }}>
      <Typography variant="h5" gutterBottom>
        Web Scraping Module
      </Typography>
      <Typography variant="body2" color="text.secondary" gutterBottom>
        Enter URLs (one per line), GitHub repositories (e.g., 'espressif/esp-idf'), and keywords (comma-separated) to scrape.
      </Typography>
      <Box component="form" noValidate autoComplete="off">
        <TextField
          label="Website URLs to Scrape"
          multiline
          rows={4}
          fullWidth
          variant="outlined"
          value={urls}
          onChange={(e) => setUrls(e.target.value)}
          margin="normal"
        />
        <TextField
          label="GitHub Repositories to Scrape"
          multiline
          rows={4}
          fullWidth
          variant="outlined"
          value={githubRepos}
          onChange={(e) => setGithubRepos(e.target.value)}
          margin="normal"
        />
        <TextField
          label="Keywords (future use)"
          fullWidth
          variant="outlined"
          value={keywords}
          onChange={(e) => setKeywords(e.target.value)}
          margin="normal"
        />
        <Box sx={{ mt: 2, display: 'flex', gap: 2, alignItems: 'center' }}>
          <Button
            variant="contained"
            color="primary"
            onClick={handleScrape}
            disabled={isLoading}
            sx={{ position: 'relative' }}
          >
            Start Scraping
            {isLoading && (
              <CircularProgress
                size={24}
                sx={{
                  position: 'absolute',
                  top: '50%',
                  left: '50%',
                  marginTop: '-12px',
                  marginLeft: '-12px',
                }}
              />
            )}
          </Button>
          <Button variant="outlined" color="secondary" disabled={true}>
            Stop Scraping
          </Button>
        </Box>
      </Box>
    </Paper>
  );
};

export default Scraping;