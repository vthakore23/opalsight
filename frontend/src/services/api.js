import axios from 'axios';

// Create axios instance
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized
      localStorage.removeItem('authToken');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// API methods
const apiService = {
  // Dashboard
  getDashboard: () => api.get('/api/dashboard'),
  getMarketOverview: () => api.get('/api/market-overview'),

  // Companies
  getCompanies: (params) => api.get('/api/companies', { params }),
  getCompany: (ticker) => api.get(`/api/company/${ticker}`),
  getCompanySentimentTimeline: (ticker) => api.get(`/api/company/${ticker}/sentiment-timeline`),
  searchCompanies: (query) => api.get('/api/search', { params: { q: query } }),

  // Reports
  getReports: () => api.get('/api/reports'),
  getReport: (id) => api.get(`/api/reports/${id}`),

  // Alerts
  getAlerts: (companyId) => api.get('/api/alerts', { params: { company_id: companyId } }),
  resolveAlert: (id) => api.post(`/api/alerts/${id}/resolve`),

  // Watchlist
  getWatchlist: (userId = 'default_user') => api.get('/api/watchlist', { params: { user_id: userId } }),
  addToWatchlist: (ticker, threshold = 0.2) => 
    api.post('/api/watchlist', { ticker, alert_threshold: threshold }),
  removeFromWatchlist: (ticker) => api.delete(`/api/watchlist/${ticker}`),

  // Collection
  runCollection: () => api.post('/api/collection/run'),
  getCollectionStatus: () => api.get('/api/collection/status'),
};

export default apiService; 