import React, { createContext, useState, useCallback, ReactNode } from 'react';

interface LogMessage {
  timestamp: string;
  message: string;
  type: 'INFO' | 'ERROR' | 'WARNING' | 'SUCCESS';
}

interface LogContextType {
  logs: LogMessage[];
  addLog: (message: string, type?: LogMessage['type']) => void;
  clearLogs: () => void;
}

export const LogContext = createContext<LogContextType>({
  logs: [],
  addLog: () => {},
  clearLogs: () => {},
});

interface LogProviderProps {
  children: ReactNode;
}

export const LogProvider = ({ children }: LogProviderProps) => {
  const [logs, setLogs] = useState<LogMessage[]>([]);

  const addLog = useCallback((message: string, type: LogMessage['type'] = 'INFO') => {
    const timestamp = new Date().toLocaleTimeString();
    setLogs((prevLogs) => [...prevLogs, { timestamp, message, type }]);
  }, []);

  const clearLogs = useCallback(() => {
    setLogs([]);
  }, []);

  const contextValue = {
    logs,
    addLog,
    clearLogs,
  };

  return (
    <LogContext.Provider value={contextValue}>
      {children}
    </LogContext.Provider>
  );
};