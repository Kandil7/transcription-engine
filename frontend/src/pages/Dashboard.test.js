import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Dashboard from '../src/pages/Dashboard';

// Mock the API calls
jest.mock('axios', () => ({
  get: jest.fn(() => Promise.resolve({ data: [] })),
}));

describe('Dashboard Component', () => {
  test('renders dashboard heading', async () => {
    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    );

    expect(screen.getByText(/Transcription Jobs/i)).toBeInTheDocument();
    
    // Wait for potential API calls to resolve
    await waitFor(() => {
      // Since we mocked the API to return empty array, 
      // we should see the "No jobs yet" message after loading
    });
  });
});