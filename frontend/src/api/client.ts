import axios from 'axios';

const API_BASE = '/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

apiClient.interceptors.response.use(
  (res) => res.data,
  (err) => {
    const message = err.response?.data?.message || err.message || 'Request failed';
    console.error(`[API Error] ${message}`);
    return Promise.reject(err);
  }
);
