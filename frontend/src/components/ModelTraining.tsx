import React, { useState, useContext } from 'react';
import {
  Box, Button, TextField, Typography, Paper, CircularProgress,
  FormControl, FormLabel, RadioGroup, FormControlLabel, Radio, Tooltip, Grid
} from '@mui/material';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import { LogContext } from '../context/LogContext';

const ModelTraining = () => {
  const [isLoading, setIsLoading] = useState(false);
  const { addLog } = useContext(LogContext);

  // Form state with default values
  const [formState, setFormState] = useState({
    model_id: 'TinyLlama/Llama-2-1b-chat-hf',
    dataset_path: 'datasheets/processed/my_datasheet_qa_gold.jsonl',
    output_dir: 'esp32_finetuned_model',
    training_method: 'qlora',
    epochs: 1,
    batch_size: 1,
    learning_rate: '2e-4',
    lora_r: 8,
    lora_alpha: 16,
    lora_dropout: 0.05,
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type } = e.target;
    setFormState(prevState => ({
      ...prevState,
      [name]: type === 'number' ? parseFloat(value) : value,
    }));
  };

  const handleStartTraining = async () => {
    setIsLoading(true);
    addLog(`Initiating '${formState.training_method}' training for model '${formState.model_id}'...`);

    const payload = {
      ...formState,
      learning_rate: parseFloat(formState.learning_rate),
    };

    try {
      const response = await fetch('http://localhost:8000/start-training/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || 'An unknown error occurred.');
      }

      addLog(`Training process started successfully. PID: ${result.pid}`, 'SUCCESS');
      addLog('Check the backend console for real-time training logs.', 'INFO');

    } catch (error: any) {
      addLog(`Failed to start training: ${error.message}`, 'ERROR');
    } finally {
      setIsLoading(false);
    }
  };

  const renderTooltip = (text: string) => (
    <Tooltip title={text} placement="top-start">
      <InfoOutlinedIcon sx={{ fontSize: 16, color: 'text.secondary', ml: 0.5 }} />
    </Tooltip>
  );

  return (
    <Paper elevation={3} sx={{ p: 3 }}>
      <Typography variant="h5" gutterBottom>
        Model Fine-Tuning
      </Typography>

      <Grid container spacing={3}>
        {/* Column 1: Core Settings */}
        <Grid item xs={12} md={6}>
          <Typography variant="h6" gutterBottom>Core Configuration</Typography>
          <TextField name="model_id" label="Base Model ID" value={formState.model_id} onChange={handleChange} fullWidth margin="normal" helperText="Model from Hugging Face Hub."/>
          <TextField name="dataset_path" label="Dataset Path" value={formState.dataset_path} onChange={handleChange} fullWidth margin="normal" helperText="Path relative to the 'data' directory."/>
          <TextField name="output_dir" label="Output Directory Name" value={formState.output_dir} onChange={handleChange} fullWidth margin="normal" helperText="Will be saved inside the 'models' directory."/>

          <FormControl component="fieldset" margin="normal">
            <FormLabel component="legend">Training Method</FormLabel>
            <RadioGroup row name="training_method" value={formState.training_method} onChange={handleChange}>
              <FormControlLabel value="qlora" control={<Radio />} label="QLoRA" />
              <FormControlLabel value="lora" control={<Radio />} label="LoRA" />
              <FormControlLabel value="full" control={<Radio />} label="Full Fine-Tune" disabled />
            </RadioGroup>
          </FormControl>
        </Grid>

        {/* Column 2: Hyperparameters */}
        <Grid item xs={12} md={6}>
          <Typography variant="h6" gutterBottom>Hyperparameters</Typography>
          <TextField name="learning_rate" label="Learning Rate" value={formState.learning_rate} onChange={handleChange} fullWidth margin="normal" />
          <TextField name="epochs" label="Epochs" type="number" value={formState.epochs} onChange={handleChange} fullWidth margin="normal" />
          <TextField name="batch_size" label="Batch Size" type="number" value={formState.batch_size} onChange={handleChange} fullWidth margin="normal" />

          {formState.training_method.includes('lora') && (
            <Box sx={{ mt: 2, p: 2, border: '1px dashed grey', borderRadius: 1 }}>
              <Typography variant="subtitle1" gutterBottom>LoRA Settings</Typography>
              <TextField name="lora_r" label="Rank (r)" type="number" value={formState.lora_r} onChange={handleChange} fullWidth margin="normal" />
              <TextField name="lora_alpha" label="Alpha" type="number" value={formState.lora_alpha} onChange={handleChange} fullWidth margin="normal" />
              <TextField name="lora_dropout" label="Dropout" type="number" value={formState.lora_dropout} onChange={handleChange} fullWidth margin="normal" />
            </Box>
          )}
        </Grid>
      </Grid>

      <Box sx={{ mt: 3 }}>
        <Button
          variant="contained"
          color="primary"
          onClick={handleStartTraining}
          disabled={isLoading}
          sx={{ position: 'relative' }}
        >
          Start Training
          {isLoading && <CircularProgress size={24} sx={{ position: 'absolute' }} />}
        </Button>
      </Box>
    </Paper>
  );
};

export default ModelTraining;