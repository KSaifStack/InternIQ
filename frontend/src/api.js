import axios from 'axios';

let backendPort = 8000;

export const setBackendPort = (port) => {
  backendPort = port;
};

const getBaseURL = () => `http://localhost:${backendPort}/api`;

const api = axios.create({ baseURL: getBaseURL() });

export const updateBaseURL = () => {
  api.defaults.baseURL = getBaseURL();
};

// === Health ===
export const checkHealth = async () => {
  try {
    const { data } = await axios.get(`http://localhost:${backendPort}/health`);
    return data.status === 'ok';
  } catch {
    return false;
  }
};

// === Jobs ===
export const getJobs = async (skip = 0, limit = 100, search = '', remote_only = false, state = '') => {
  const params = { skip, limit };
  if (search) params.search = search;
  if (remote_only) params.remote_only = true;
  if (state) params.state = state;
  const { data } = await api.get('/jobs/', { params, timeout: 10000 });
  return data;
};

export const getStates = async () => {
  const { data } = await api.get('/jobs/states');
  return data;
};

export const getSources = async () => {
  const { data } = await api.get('/jobs/sources');
  return data;
};

export const triggerSync = async () => {
  const { data } = await api.post('/jobs/sync');
  return data;
};

export const getSyncLogs = async (limit = 50) => {
  const { data } = await api.get('/jobs/sync-log', { params: { limit } });
  return data.logs || [];
};

export const hideJob = async (job_id) => {
  const { data } = await api.post(`/jobs/${job_id}/hide`);
  return data;
};

// === Applications ===
export const getApplications = async (user_id) => {
  const { data } = await api.get(`/applications/user/${user_id}`);
  return data;
};

export const createApplication = async (user_id, job_id, notes = '') => {
  const { data } = await api.post(`/applications/user/${user_id}`, { job_id, notes });
  return data;
};

export const updateApplication = async (app_id, status) => {
  const { data } = await api.put(`/applications/${app_id}`, { status });
  return data;
};

export const deleteApplication = async (app_id) => {
  const { data } = await api.delete(`/applications/${app_id}`);
  return data;
};

// === Users ===
export const getUser = async (user_id) => {
  const { data } = await api.get(`/users/${user_id}`);
  return data;
};

export const updateUser = async (user_id, updates) => {
  const { data } = await api.put(`/users/${user_id}`, updates);
  return data;
};

// === Pipeline / Admin ===
export const getPipelineStatus = async () => {
  const { data } = await api.get('/pipeline/status');
  return data;
};

export const getSystemHealth = async () => {
  const { data } = await api.get('/admin/health');
  return data;
};

// === Insights ===
export const getTrendingSearches = async (limit = 8) => {
  const { data } = await api.get('/insights/trending-searches', { params: { limit } });
  return data;
};

export const getTrendingSkills = async (limit = 10) => {
  const { data } = await api.get('/insights/trending-skills', { params: { limit } });
  return data;
};

// === Activity ===
export const logActivity = async (activity_type, job_id = null, metadata = null) => {
  await api.post('/activity/log', { activity_type, job_id, metadata });
};

export default api;
