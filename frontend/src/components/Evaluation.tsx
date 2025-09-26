import React, { useState, useContext } from 'react';
import { Box, Button, TextField, Typography, Paper, CircularProgress, Accordion, AccordionSummary, AccordionDetails, Divider } from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { LogContext } from '../context/LogContext';

const Evaluation = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [report, setReport] = useState<any>(null);
  const { addLog } = useContext(LogContext);

  // State for prediction generation form
  const [predictionForm, setPredictionForm] = useState({
    base_model_id: 'TinyLlama/Llama-2-1b-chat-hf',
    adapter_path: 'esp32_finetuned_model/final_model',
    dataset_path: 'datasheets/processed/my_datasheet_qa_gold.jsonl',
    output_dir: 'predictions'
  });

  // State for evaluation form
  const [evaluationForm, setEvaluationForm] = useState({
    gold_file_path: 'datasheets/processed/my_datasheet_qa_gold.jsonl',
    pred_file_path: 'predictions/qa_pred.jsonl'
  });

  const handlePredictionChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setPredictionForm(prevState => ({ ...prevState, [name]: value }));
  };

  const handleEvaluationChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setEvaluationForm(prevState => ({ ...prevState, [name]: value }));
  };

  const handleApiCall = async (endpoint: string, payload: any, logMessage: string) => {
    setIsLoading(true);
    setReport(null);
    addLog(`${logMessage}...`);

    try {
      const response = await fetch(`http://localhost:8000${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || 'An unknown error occurred.');
      }

      addLog(`${logMessage} completed.`, 'SUCCESS');
      if (endpoint === '/evaluate-predictions/') {
        setReport(result); // Only set report for evaluation results
      } else {
         addLog(`Process started with PID: ${result.pid}`, 'INFO');
      }

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
        Model Evaluation
      </Typography>

      {/* Step 1: Generate Predictions */}
      <Box sx={{ my: 2 }}>
        <Typography variant="h6">Step 1: Generate Predictions</Typography>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          Use a trained model to generate answers for a test dataset.
        </Typography>
        <TextField name="base_model_id" label="Base Model ID" value={predictionForm.base_model_id} onChange={handlePredictionChange} fullWidth margin="normal"/>
        <TextField name="adapter_path" label="Adapter Path (from 'models' dir, optional)" value={predictionForm.adapter_path} onChange={handlePredictionChange} fullWidth margin="normal"/>
        <TextField name="dataset_path" label="Test Dataset Path (from 'data' dir)" value={predictionForm.dataset_path} onChange={handlePredictionChange} fullWidth margin="normal"/>
        <Button
          variant="contained"
          onClick={() => handleApiCall('/generate-predictions/', predictionForm, 'Prediction generation')}
          disabled={isLoading}
        >
          Generate Predictions
        </Button>
      </Box>

      <Divider sx={{ my: 4 }} />

      {/* Step 2: Run Evaluation */}
      <Box sx={{ my: 2 }}>
        <Typography variant="h6">Step 2: Evaluate Predictions</Typography>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          Compare the generated predictions against the ground truth answers.
        </Typography>
        <TextField name="gold_file_path" label="Ground Truth File Path (from 'data' dir)" value={evaluationForm.gold_file_path} onChange={handleEvaluationChange} fullWidth margin="normal"/>
        <TextField name="pred_file_path" label="Prediction File Path (from 'reports' dir)" value={evaluationForm.pred_file_path} onChange={handleEvaluationChange} fullWidth margin="normal"/>
        <Button
          variant="contained"
          onClick={() => handleApiCall('/evaluate-predictions/', evaluationForm, 'Evaluation')}
          disabled={isLoading}
        >
          Run Evaluation
        </Button>
      </Box>

      {/* Results Section */}
      {isLoading && <CircularProgress sx={{ display: 'block', margin: '20px auto' }} />}
      {report && (
        <Box sx={{ mt: 4 }}>
          <Typography variant="h6">Evaluation Report</Typography>
          <Accordion defaultExpanded>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography>Summary</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Typography>Total Questions: {report.total_questions || 'N/A'}</Typography>
              <Typography>Exact Match: {report.exact_match?.toFixed(2) || '0.00'}%</Typography>
              <Typography>F1 Score: {report.f1_score?.toFixed(2) || '0.00'}%</Typography>
            </AccordionDetails>
          </Accordion>
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography>View Full JSON Report</Typography>
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

export default Evaluation;