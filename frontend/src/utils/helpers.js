// Utility functions for common operations

// Function to format file sizes
export const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// Function to format duration in seconds to MM:SS
export const formatDuration = (seconds) => {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
};

// Function to format large numbers with commas
export const formatNumber = (num) => {
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
};

// Function to download content as a file
export const downloadFile = (content, filename, mimeType = 'text/plain') => {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
};

// Function to get status color based on status
export const getStatusColor = (status) => {
  const colors = {
    pending: 'warning',
    processing: 'info',
    completed: 'success',
    failed: 'error',
    cancelled: 'default'
  };
  return colors[status] || 'default';
};

// Function to get emotion color
export const getEmotionColor = (emotion) => {
  const colors = {
    happy: '#4caf50',
    sad: '#2196f3',
    angry: '#f44336',
    neutral: '#9e9e9e',
    excited: '#ff9800',
    calm: '#00bcd4',
    confident: '#8bc34a',
    nervous: '#ff5722'
  };
  return colors[emotion] || colors.neutral;
};

// Function to get speaker color
export const getSpeakerColor = (speaker, index) => {
  const colors = [
    '#e3f2fd', '#f3e5f5', '#e8f5e8', '#fff3e0', '#fce4ec',
    '#f1f8e9', '#e0f2f1', '#f9fbe7', '#efebe9', '#fafafa'
  ];
  return colors[index % colors.length];
};

// Function to debounce a function
export const debounce = (func, wait) => {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
};

// Function to validate email
export const isValidEmail = (email) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

// Function to validate URL
export const isValidUrl = (url) => {
  try {
    new URL(url);
    return true;
  } catch (e) {
    return false;
  }
};