import React, { useState, useContext } from 'react';
import { Box, Button, TextField, Typography, Paper, CircularProgress, Accordion, AccordionSummary, AccordionDetails } from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { LogContext } from '../context/LogContext';

const DataManagement = () => {
  const [codePath, setCodePath] = useState('github/espressif_esp-idf');
  const [datasheetPath, setDatasheetPath] = useState('datasheets');
  const [isLoading, setIsLoading] = useState(false);
  const [report, setReport] = useState<any>(null);
  const { addLog } = useContext(LogContext);

  const handleApiCall = async (endpoint: string, path: string, logMessage: string) => {
    setIsLoading(true);
    setReport(null);
    addLog(`${logMessage} for directory: ${path}`);

    try {
      const response = await fetch(`http://localhost:8000${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ path }),
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || 'An unknown error occurred.');
      }

      addLog(`${logMessage} completed.`, 'SUCCESS');
      setReport(result);

    } catch (error: any) {
      addLog(`Error during ${logMessage.toLowerCase()}: ${error.message}`, 'ERROR');
      setReport({ error: error.message });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Paper elevation={3} sx={{ p: 3 }}>
      <Typography variant="h5" gutterBottom>
        Data Management & QA
      </Typography>

      {/* Code Analysis Section */}
      <Box sx={{ my: 2 }}>
        <Typography variant="h6">Code Quality Analysis</Typography>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          Analyze scraped source code for quality metrics, licenses, and secrets. Provide the path relative to the 'data' directory.
        </Typography>
        <TextField
          label="Code Directory Path"
          fullWidth
          variant="outlined"
          value={codePath}
          onChange={(e) => setCodePath(e.target.value)}
          margin="normal"
        />
        <Button
          variant="contained"
          onClick={() => handleApiCall('/analyze-code/', codePath, 'Code analysis')}
          disabled={isLoading || !codePath}
        >
          Analyze Code
        </Button>
      </Box>

      {/* Datasheet Processing Section */}
      <Box sx={{ my: 4 }}>
        <Typography variant="h6">Datasheet Processing</Typography>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          Process PDF datasheets to extract text and generate structured QA pairs. Provide the path relative to the 'data' directory.
        </Typography>
        <TextField
          label="Datasheet Directory Path"
          fullWidth
          variant="outlined"
          value={datasheetPath}
          onChange={(e) => setDatasheetPath(e.target.value)}
          margin="normal"
        />
        <Button
          variant="contained"
          onClick={() => handleApiCall('/process-datasheets/', datasheetPath, 'Datasheet processing')}
          disabled={isLoading || !datasheetPath}
        >
          Process Datasheets
        </Button>
      </Box>

      {/* Results Section */}
      {isLoading && <CircularProgress sx={{ display: 'block', margin: '20px auto' }} />}
      {report && (
        <Box sx={{ mt: 4 }}>
          <Typography variant="h6">Result</Typography>
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography>View JSON Report</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Paper component="pre" sx={{ p: 2, overflowX: 'auto', maxHeight: '400px', backgroundColor: 'background.default' }}>
                {JSON.stringify(report, null, 2)}
              </Paper>
            </AccordionDetails>
          </Accordion>
        </Box>
      )}
    </Paper>
  );
};

export default DataManagement;