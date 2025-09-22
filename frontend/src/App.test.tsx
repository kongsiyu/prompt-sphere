import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import App from './App';

describe('App', () => {
  it('renders the main heading', () => {
    render(<App />);
    expect(screen.getByText('AI System Prompt Generator')).toBeInTheDocument();
  });

  it('renders Vite and React logos', () => {
    render(<App />);
    expect(screen.getByAltText('Vite logo')).toBeInTheDocument();
    expect(screen.getByAltText('React logo')).toBeInTheDocument();
  });

  it('has a working counter button', () => {
    render(<App />);
    const button = screen.getByRole('button', { name: /count is 0/i });
    expect(button).toBeInTheDocument();

    fireEvent.click(button);
    expect(screen.getByRole('button', { name: /count is 1/i })).toBeInTheDocument();
  });

  it('displays HMR instruction text', () => {
    render(<App />);
    expect(screen.getByText('src/App.tsx')).toBeInTheDocument();
    expect(screen.getByText((content) => content.includes('save to test HMR'))).toBeInTheDocument();
  });
});