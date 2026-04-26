import axios from 'axios';

// Determine the API base URL
// On Vercel (production), use relative path since frontend and backend share the same domain
// In development, use the VITE_API_URL env var or localhost fallback
const isProduction = import.meta.env.PROD;
const envApiUrl = import.meta.env.VITE_API_URL;

let API_BASE_URL;
if (isProduction) {
  // In production on Vercel, use relative path
  API_BASE_URL = '/api/v1';
} else if (envApiUrl) {
  API_BASE_URL = envApiUrl;
} else {
  API_BASE_URL = 'http://localhost:8000/api/v1';
}

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
