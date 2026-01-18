import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import App from '../src/App';

// Mock the API calls
jest.mock('../src/services/api', () => ({
  getJobs: jest.fn(() => Promise.resolve([])),
  getJobDetails: jest.fn(() => Promise.resolve({ id: 'test-job', status: 'completed', progress: 100 })),
}));

describe('App Component', () => {
  test('renders header with navigation links', () => {
    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    );

    expect(screen.getByText(/Transcription Engine/i)).toBeInTheDocument();
    expect(screen.getByText(/Dashboard/i)).toBeInTheDocument();
    expect(screen.getByText(/Upload/i)).toBeInTheDocument();
    expect(screen.getByText(/Live Stream/i)).toBeInTheDocument();
    expect(screen.getByText(/Help/i)).toBeInTheDocument();
    expect(screen.getByText(/Settings/i)).toBeInTheDocument();
  });
});

// Additional tests would go here for each component
// This is a basic test suite structure