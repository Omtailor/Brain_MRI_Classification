/**
 * API Service
 * Centralized API communication for BrainScan AI frontend
 */

// Use Vite's same-origin proxy in development so the browser does not reject
// responses when Vite selects a different host or port.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

/**
 * Analyze MRI file using the backend API
 * @param {File} file - The MRI file to analyze
 * @returns {Promise<Object>} - The analysis result from the backend
 * @throws {Error} - With user-friendly error message
 */
export async function analyzeMRI(file) {
  if (!file) {
    throw new Error('No file provided for analysis');
  }

  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await fetch(`${API_BASE_URL}/api/analyze`, {
      method: 'POST',
      body: formData,
    });

    // Handle non-JSON responses
    const contentType = response.headers.get('content-type');
    if (!contentType || !contentType.includes('application/json')) {
      throw new Error('Invalid response from server');
    }

    const data = await response.json();

    if (!response.ok) {
      // Handle specific HTTP status codes
      switch (response.status) {
        case 400:
          throw new Error(data.message || data.detail || 'Invalid request. Please check your file.');
        case 413:
          throw new Error('File is too large. Maximum size is 20 MB.');
        case 422:
          throw new Error(data.message || data.detail || 'Invalid file format. Please upload a valid MRI image or PDF.');
        case 500:
          throw new Error('Server error occurred while processing the MRI. Please try again.');
        case 502:
        case 503:
          throw new Error('Analysis service is temporarily unavailable. Please try again later.');
        default:
          throw new Error(data.message || data.detail || 'Failed to analyze the MRI. Please try again.');
      }
    }

    // Validate response structure
    if (!data || typeof data !== 'object') {
      throw new Error('Invalid response format from server');
    }

    return data;
  } catch (error) {
    // Handle network errors
    if (error.name === 'TypeError' && error.message === 'Failed to fetch') {
      throw new Error('Unable to connect to the analysis service. Please check your connection and try again.', { cause: error });
    }

    // Re-throw API errors with user-friendly messages
    if (error.message) {
      throw error;
    }

    throw new Error('Something went wrong while analyzing the MRI. Please try again.', { cause: error });
  }
}


