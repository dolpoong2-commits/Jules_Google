import React, { createContext, useState, useMemo, ReactNode } from 'react';
import { createTheme, ThemeProvider as MuiThemeProvider } from '@mui/material/styles';
import { PaletteMode } from '@mui/material';

interface ThemeContextType {
  toggleTheme: () => void;
  mode: PaletteMode;
}

export const ThemeContext = createContext<ThemeContextType>({
  toggleTheme: () => {},
  mode: 'dark',
});

interface CustomThemeProviderProps {
  children: ReactNode;
}

export const CustomThemeProvider = ({ children }: CustomThemeProviderProps) => {
  const [mode, setMode] = useState<PaletteMode>('dark');

  const toggleTheme = () => {
    setMode((prevMode) => (prevMode === 'light' ? 'dark' : 'light'));
  };

  const theme = useMemo(
    () =>
      createTheme({
        palette: {
          mode,
          ...(mode === 'dark'
            ? {
                // Vivid dark mode palette
                primary: {
                  main: '#00BFFF', // DeepSkyBlue
                },
                secondary: {
                  main: '#FF69B4', // HotPink
                },
                background: {
                  default: '#1a1a2e', // Dark blue-ish background
                  paper: '#162447',
                },
                text: {
                    primary: '#e4f9f5',
                    secondary: '#b8b8d1'
                }
              }
            : {
                // Modern light mode palette
                primary: {
                  main: '#6200ea', // Deep Purple
                },
                secondary: {
                  main: '#03dac6', // Teal
                },
                background: {
                  default: '#f7f8fc',
                  paper: '#ffffff',
                },
              }),
        },
        typography: {
            fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
            h5: {
                fontWeight: 700,
            },
        },
        components: {
            MuiAppBar: {
                styleOverrides: {
                    root: {
                        background: mode === 'dark' ? 'linear-gradient(45deg, #162447 30%, #1f4068 90%)' : 'linear-gradient(45deg, #6200ea 30%, #3700b3 90%)',
                        boxShadow: '0 3px 5px 2px rgba(0, 0, 0, .3)',
                    }
                }
            }
        }
      }),
    [mode]
  );

  return (
    <ThemeContext.Provider value={{ toggleTheme, mode }}>
      <MuiThemeProvider theme={theme}>{children}</MuiThemeProvider>
    </ThemeContext.Provider>
  );
};