import React, { useContext, useEffect, useRef } from 'react';
import { Paper, Typography, Box } from '@mui/material';
import { LogContext } from '../context/LogContext';

const LogPanel = () => {
  const { logs } = useContext(LogContext);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Scroll to the bottom whenever new logs are added
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  const getLogColor = (type: string) => {
    switch (type) {
      case 'ERROR':
        return 'error.main';
      case 'WARNING':
        return 'warning.main';
      case 'SUCCESS':
        return 'success.main';
      default:
        return 'text.primary';
    }
  };

  return (
    <Paper
      elevation={3}
      sx={{
        mt: 2,
        p: 2,
        flexShrink: 0,
        height: '250px',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <Typography variant="h6" gutterBottom>
        Logs
      </Typography>
      <Box
        ref={scrollRef}
        sx={{
          flexGrow: 1,
          overflowY: 'auto',
          fontFamily: 'monospace',
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-all',
          fontSize: '0.875rem',
          '&::-webkit-scrollbar': {
            width: '0.4em'
          },
          '&::-webkit-scrollbar-track': {
            boxShadow: 'inset 0 0 6px rgba(0,0,0,0.00)',
            webkitBoxShadow: 'inset 0 0 6px rgba(0,0,0,0.00)'
          },
          '&::-webkit-scrollbar-thumb': {
            backgroundColor: 'rgba(0,0,0,.1)',
            outline: '1px solid slategrey'
          }
        }}
      >
        {logs.map((log, index) => (
          <Box key={index} component="div" sx={{ color: getLogColor(log.type) }}>
            <Typography component="span" variant="body2" sx={{ color: 'text.secondary' }}>
              [{log.timestamp}]
            </Typography>
            <Typography component="span" variant="body2" sx={{ ml: 1, color: 'inherit' }}>
              [{log.type}]
            </Typography>
            <Typography component="span" variant="body2" sx={{ ml: 1, color: 'inherit' }}>
              {log.message}
            </Typography>
          </Box>
        ))}
      </Box>
    </Paper>
  );
};

export default LogPanel;