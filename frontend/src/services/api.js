import axios from 'axios';

// Determine the API base URL
// In development: uses VITE_API_URL or localhost fallback
// In production: uses VITE_API_URL (must be set in Vercel environment)
const envApiUrl = import.meta.env.VITE_API_URL;

const API_BASE_URL = envApiUrl || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const message = error.response?.data?.detail || error.message || 'Произошла ошибка';
    return Promise.reject(new Error(message));
  }
);

// Filials API
export const filialsApi = {
  getAll: () => api.get('/filials'),
  getById: (id) => api.get(`/filials/${id}`),
  create: (data) => api.post('/filials', data),
  update: (id, data) => api.put(`/filials/${id}`, data),
  updateNextRevision: (id, next_revision_date, status) => api.put(`/filials/${id}/next-revision`, { next_revision_date, status }),
  delete: (id) => api.delete(`/filials/${id}`),
};

export default api;
