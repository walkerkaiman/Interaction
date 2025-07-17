import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000'; // Updated to match backend

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
});

// Example: Get all modules
export const fetchModules = async () => {
  const response = await api.get('/modules');
  // Convert object to array if needed
  const modulesObj = response.data;
  return Array.isArray(modulesObj) ? modulesObj : Object.values(modulesObj);
};

// Get information about currently running module instances
export const fetchModuleInstances = async () => {
  const response = await api.get('/module_instances');
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

// Delete a specific interaction by index
export const deleteInteraction = async (index: number) => {
  const response = await api.post('/config/delete_interaction', { index });
  return response.data;
};

// Module notes API
export const getModuleNotes = async (moduleId: string) => {
  const response = await api.get(`/module_notes/${moduleId}`);
  return response.data.notes;
};

export const saveModuleNotes = async (moduleId: string, notes: string) => {
  const response = await api.post(`/module_notes/${moduleId}`, { notes });
  return response.data;
};

export default api; 