import axios from 'axios';
import { useAuthStore } from '@/store/auth'; // Assuming Pinia store for auth

// Determine the base URL for the API
// In a Vite project, environment variables are accessed via import.meta.env
const API_BASE_URL = import.meta.env.VITE_APP_API_URL || 'http://localhost:8000/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor to add the auth token to requests
apiClient.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore();
    const token = authStore.token;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Interceptor to handle 401 errors (e.g., token expired)
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response && error.response.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const authStore = useAuthStore();
      try {
        // Attempt to refresh token here if your API supports it
        // For now, we'll just log out the user as a simple example
        console.error('API request failed with 401, attempting to re-authenticate or logout.');
        await authStore.logout(); // Or a refresh token mechanism
        // Optionally, redirect to login page
        // window.location.href = '/login'; 
        return Promise.reject(error.response.data); // Or a new request with new token
      } catch (refreshError) {
        return Promise.reject(refreshError);
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;

// You can also export specific API call functions from here if you prefer
// Example:
// export const fetchTickets = (params) => apiClient.get('/tickets/', { params });
// export const getTicketDetails = (id) => apiClient.get(`/tickets/${id}/`);
// export const createTicket = (data) => apiClient.post('/tickets/', data);

