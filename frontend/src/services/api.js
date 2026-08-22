import axios from 'axios';

// Base API URL from Vite environment variable (e.g. https://your-backend.vercel.app)
export const API_URL = (import.meta.env.VITE_API_URL || '').replace(/\/+$/, '');

const API = axios.create({
  baseURL: API_URL,
  timeout: 25000,
});

// Helper to resolve backend image paths (uploads and sample images) across separate domains
export const getImageUrl = (path) => {
  if (!path) return '';
  if (path.startsWith('http://') || path.startsWith('https://') || path.startsWith('blob:') || path.startsWith('data:')) {
    return path;
  }
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return `${API_URL}${cleanPath}`;
};

// Attach Authorization header if JWT token exists in localStorage
API.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('freshco_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Intercept errors and format network/timeout messages
API.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
      error.customMessage = 'Request timed out. The server took too long to respond. Please check your connection and retry.';
    } else if (!error.response) {
      error.customMessage = 'Network error. Unable to reach the server. Please check your backend URL and network connection.';
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  register: (data) => API.post('/api/auth/register', data),
  login: (data) => API.post('/api/auth/login', data),
  getMe: () => API.get('/api/auth/me'),
  requestPasswordReset: (data) => API.post('/api/auth/forgot-password/request', data),
  verifyResetCode: (data) => API.post('/api/auth/forgot-password/verify-code', data),
  resetPassword: (data) => API.post('/api/auth/forgot-password/reset', data),
};

export const predictAPI = {
  predictImage: (formData) =>
    API.post('/api/predict', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }),
  getSamples: () => API.get('/api/predict/samples'),
};

export const historyAPI = {
  getHistory: (params = {}) => API.get('/api/history', { params }),
  getStats: () => API.get('/api/history/stats'),
  deleteRecord: (id) => API.delete(`/api/history/${id}`),
  clearHistory: () => API.delete('/api/history'),
};

export const analyticsAPI = {
  getAnalytics: (range = 'week') => API.get('/api/analytics', { params: { range } }),
};

export const adminAPI = {
  getStats: () => API.get('/api/admin/stats'),
  getUsers: (params = {}) => API.get('/api/admin/users', { params }),
  getUserDetail: (userId) => API.get(`/api/admin/users/${userId}`),
  toggleUserStatus: (userId, data) => API.patch(`/api/admin/users/${userId}/status`, data),
  getLogs: (limit = 50) => API.get('/api/admin/logs', { params: { limit } }),
};

export const agentAPI = {
  getMultiItemRecipe: (days = 7) => API.post(`/api/agent/recipe-suggestion?days=${days}`),
};

export default API;
