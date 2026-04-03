import axios from 'axios';
import { fetchAuthSession } from 'aws-amplify/auth';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use(
  async (config) => {
    try {
      const session = await fetchAuthSession();
      const token = session.tokens?.idToken?.toString();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    } catch (error) {
      console.error('Failed to get auth token:', error);
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 422) {
      const detail = error.response.data?.detail;
      if (Array.isArray(detail)) {
        const errorMessage = detail.map(err => err.msg || err).join(', ');
        alert(`バリデーションエラー: ${errorMessage}`);
      } else {
        alert('バリデーションエラーが発生しました');
      }
    } else if (error.code === 'ECONNABORTED') {
      alert('リクエストがタイムアウトしました');
    } else if (!error.response) {
      alert('ネットワークエラーが発生しました');
    }
    return Promise.reject(error);
  }
);

export default apiClient;
