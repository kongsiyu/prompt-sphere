import React from 'react';
import AppRouter from './router';
import { ThemeProvider } from './contexts/ThemeContext';
import './App.css';

/**
 * 主应用组件
 */
function App() {
  return (
    <ThemeProvider>
      <AppRouter />
    </ThemeProvider>
  );
}

export default App;