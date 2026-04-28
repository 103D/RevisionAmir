import axios from 'axios';

// Determine the API base URL
const envApiUrl = import.meta.env.VITE_API_URL;
const API_BASE_URL = envApiUrl || 'http://localhost:8000/api/v1';

// Regular API client (JSON responses)
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Response interceptor for JSON responses
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const message = error.response?.data?.detail || error.message || 'Произошла ошибка';
    return Promise.reject(new Error(message));
  }
);

// Raw API client for file downloads (no response transformation)
const rawApi = axios.create({
  baseURL: API_BASE_URL,
  responseType: 'blob',
});

// Filials API
export const filialsApi = {
  getAll: () => api.get('/filials'),
  getById: (id) => api.get(`/filials/${id}`),
  create: (data) => api.post('/filials', data),
  update: (id, data) => api.put(`/filials/${id}`, data),
  updateNextRevision: (id, next_revision_date, status) => api.put(`/filials/${id}/next-revision`, { next_revision_date, status }),
  delete: (id) => api.delete(`/filials/${id}`),
};

// Export API using rawApi for binary downloads
export const exportApi = {
  downloadFilials: async () => {
    try {
      const response = await rawApi.get('/export/filials');
      const url = window.URL.createObjectURL(new Blob([response.data], { type: response.headers['content-type'] || 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' }));
      const link = document.createElement('a');
      link.href = url;
      link.download = 'filials.xlsx';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      throw new Error(error.message || 'Не удалось скачать филиалы');
    }
  },
  downloadHolidays: async () => {
    try {
      const response = await rawApi.get('/export/holidays');
      const url = window.URL.createObjectURL(new Blob([response.data], { type: response.headers['content-type'] || 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' }));
      const link = document.createElement('a');
      link.href = url;
      link.download = 'holidays.xlsx';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      throw new Error(error.message || 'Не удалось скачать праздники');
    }
  },
};

export default api;
