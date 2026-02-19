import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for adding auth token
api.interceptors.request.use(
  (config) => {
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

// Response interceptor for handling errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('authToken');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Orders API (trailing slash для списков — избегаем 307 редиректа за прокси /api/)
export const ordersAPI = {
  getOrders: (params = {}) => api.get('/orders/', { params }),
  getOrder: (id) => api.get(`/orders/${id}`),
  createOrder: (data) => api.post('/orders/', data),
  updateOrder: (id, data) => api.put(`/orders/${id}`, data),
  deleteOrder: (id) => api.delete(`/orders/${id}`),
  getOrderMessages: (id) => api.get(`/orders/${id}/messages`),
  addOrderMessage: (id, message) => api.post(`/orders/${id}/messages`, { message_text: message }),
  acceptOrder: (id, supplierId) => api.post(`/orders/${id}/accept`, { supplier_id: supplierId }),
  declineOrder: (id, supplierId) => api.post(`/orders/${id}/decline`, { supplier_id: supplierId }),
  completeOrder: (id, supplierId) => api.post(`/orders/${id}/complete`, { supplier_id: supplierId }),
  cancelOrder: (id, supplierId) => api.post(`/orders/${id}/cancel`, { supplier_id: supplierId }),
};

// Suppliers API
export const suppliersAPI = {
  getSuppliers: (params = {}) => api.get('/suppliers/', { params }),
  getSupplier: (id) => api.get(`/suppliers/${id}`),
  createSupplier: (data) => api.post('/suppliers/', data),
  updateSupplier: (id, data) => api.put(`/suppliers/${id}`, data),
  deleteSupplier: (id) => api.delete(`/suppliers/${id}`),
  activateSupplier: (id) => api.post(`/suppliers/${id}/activate`),
  deactivateSupplier: (id) => api.post(`/suppliers/${id}/deactivate`),
  getSupplierFilters: (id) => api.get(`/suppliers/${id}/filters`),
  getSupplierOrders: (id, params = {}) => api.get(`/suppliers/${id}/orders`, { params }),
};

// Filters API
export const filtersAPI = {
  getFilters: (params = {}) => api.get('/filters/', { params }),
  getFilter: (id) => api.get(`/filters/${id}`),
  createFilter: (data) => api.post('/filters/', data),
  updateFilter: (id, data) => api.put(`/filters/${id}`, data),
  deleteFilter: (id) => api.delete(`/filters/${id}`),
  activateFilter: (id) => api.post(`/filters/${id}/activate`),
  deactivateFilter: (id) => api.post(`/filters/${id}/deactivate`),
  createBulkFilters: (supplierId, keywords) => api.post('/filters/bulk', { supplier_id: supplierId, keywords }),
};

// Stats API
export const statsAPI = {
  getStats: (params = {}) => api.get('/stats/', { params }),
  getDailyStats: (params = {}) => api.get('/stats/orders/daily', { params }),
  getSupplierPerformance: (params = {}) => api.get('/stats/suppliers/performance', { params }),
  getActivityStats: (params = {}) => api.get('/stats/activity', { params }),
  getOrderStatusDistribution: (params = {}) => api.get('/stats/orders/status-distribution', { params }),
};

// Activity API
export const activityAPI = {
  getActivityLogs: (params = {}) => api.get('/activity/', { params }),
  getAvailableActions: () => api.get('/activity/actions'),
  getRecentActivity: (params = {}) => api.get('/activity/recent', { params }),
  getUserActivity: (userId, params = {}) => api.get(`/activity/user/${userId}`, { params }),
};

export default api;
