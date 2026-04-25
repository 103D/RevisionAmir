import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

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
