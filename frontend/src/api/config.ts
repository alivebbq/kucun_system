import axios from 'axios';
import { useUserStore } from '../stores/user';
import router from '../router';

export const api = axios.create({
    baseURL: 'http://localhost:8000',  // 直接使用完整的后端地址
    timeout: 10000,  // 增加超时时间
    withCredentials: true,
    headers: {
        'Accept': 'application/json'
    }
});

// 请求拦截器
api.interceptors.request.use(
    (config) => {
        console.log('=== API Request ===', {
            url: config.url,
            method: config.method,
            params: config.params,
            headers: config.headers
        });

        const userStore = useUserStore();
        // 如果有 token，添加到请求头
        if (userStore.token) {
            config.headers.Authorization = `Bearer ${userStore.token}`;
            console.log('Adding token to request:', `Bearer ${userStore.token}`);
        }

        return config;
    },
    (error) => {
        console.error('Request error:', error);
        return Promise.reject(error);
    }
);

// 响应拦截器
api.interceptors.response.use(
    (response) => {
        console.log('=== API Response ===', {
            status: response.status,
            statusText: response.statusText,
            headers: response.headers,
            data: response.data
        });
        return response.data;
    },
    async (error) => {
        // 添加重试逻辑
        if (!error.config.__retryCount) {
            error.config.__retryCount = 0;
        }

        if (error.config.__retryCount < 2) {  // 最多重试2次
            error.config.__retryCount++;

            // 延迟重试
            await new Promise(resolve => setTimeout(resolve, 1000));

            return api.request(error.config);
        }

        // 如果是网络错误，尝试重试
        if (error.message === 'Network Error' && error.config && !error.config.__isRetry) {
            error.config.__isRetry = true;
            try {
                return await api.request(error.config);
            } catch (retryError) {
                return Promise.reject(retryError);
            }
        }
        console.error('=== API Error ===', {
            name: error.name,
            message: error.message,
            response: {
                status: error.response?.status,
                statusText: error.response?.statusText,
                data: error.response?.data,
                headers: error.response?.headers
            },
            config: {
                url: error.config?.url,
                method: error.config?.method,
                headers: error.config?.headers,
                data: error.config?.data
            }
        });

        if (error.response) {
            const userStore = useUserStore();
            switch (error.response.status) {
                case 401:
                    userStore.logout();
                    router.push('/login');
                    break;
                case 403:
                    router.push('/');
                    break;
                case 404:
                    console.error('API endpoint not found:', error.config?.url);
                    break;
            }
        }
        return Promise.reject(error);
    }
);

export default api; 