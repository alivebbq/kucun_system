import axios from 'axios';

const baseURL = 'http://localhost:8000/api/v1';

const api = axios.create({
    baseURL,
    timeout: 5000,
    headers: {
        'Content-Type': 'application/json',
    },
});

// 响应拦截器
api.interceptors.response.use(
    (response) => response.data,
    (error) => {
        console.error('API错误:', error);
        return Promise.reject(error);
    }
);

export default api; 