import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api'; // Adjust as needed

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
});

// Example: Get all modules
export const fetchModules = async () => {
  const response = await api.get('/modules');
  return response.data;
};

// Example: Get global config
export const fetchConfig = async () => {
  const response = await api.get('/config');
  return response.data;
};

// Example: Update config
export const updateConfig = async (config: any) => {
  const response = await api.post('/config', config);
  return response.data;
};

// Add more API endpoints as needed

export default api; 