import { useState, useEffect } from 'react';
import axios from 'axios';
import { useSnackbar } from 'notistack';

// Custom hook for API calls with error handling
export const useApiCall = () => {
  const { enqueueSnackbar } = useSnackbar();

  const apiCall = async (method, url, data = null, options = {}) => {
    try {
      let response;
      
      if (method.toLowerCase() === 'get') {
        response = await axios.get(url, options);
      } else if (method.toLowerCase() === 'post') {
        response = await axios.post(url, data, options);
      } else if (method.toLowerCase() === 'put') {
        response = await axios.put(url, data, options);
      } else if (method.toLowerCase() === 'delete') {
        response = await axios.delete(url, options);
      } else {
        throw new Error(`Unsupported method: ${method}`);
      }
      
      return response.data;
    } catch (error) {
      console.error('API call error:', error);
      
      // Determine error message based on error type
      let errorMessage = 'An unexpected error occurred';
      
      if (error.response) {
        // Server responded with error status
        errorMessage = error.response.data.detail || `Server error: ${error.response.status}`;
      } else if (error.request) {
        // Request was made but no response received
        errorMessage = 'Network error: Unable to reach the server';
      } else {
        // Something else happened
        errorMessage = error.message || 'An unexpected error occurred';
      }
      
      // Show error notification
      enqueueSnackbar(errorMessage, { variant: 'error' });
      
      // Re-throw the error so calling code can handle it if needed
      throw error;
    }
  };

  return { apiCall };
};

// Custom hook for fetching data with loading state
export const useFetchData = (url, deps = []) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { enqueueSnackbar } = useSnackbar();

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await axios.get(url);
        setData(response.data);
      } catch (err) {
        console.error('Fetch error:', err);
        setError(err);
        enqueueSnackbar('Failed to load data', { variant: 'error' });
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, deps); // eslint-disable-line react-hooks/exhaustive-deps

  return { data, loading, error };
};

// Custom hook for form submission with loading state
export const useFormSubmit = (submitFunction) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const { enqueueSnackbar } = useSnackbar();

  const submit = async (...args) => {
    try {
      setLoading(true);
      setError(null);
      const result = await submitFunction(...args);
      return result;
    } catch (err) {
      console.error('Form submission error:', err);
      setError(err);
      enqueueSnackbar('Submission failed', { variant: 'error' });
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return { submit, loading, error };
};