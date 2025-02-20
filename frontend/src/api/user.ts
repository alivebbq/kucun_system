import api from './config';

export interface User {
    id: number;
    username: string;
    name: string | null;
    is_owner: boolean;
    permissions: string[];
    created_at: string;
    last_login: string | null;
}

export interface LoginResponse {
    access_token: string;
    token_type: string;
    user: User;
}

export const login = (username: string, password: string) => {
    const params = new URLSearchParams();
    params.append('username', username);
    params.append('password', password);

    console.log('Sending login request with params:', {
        username,
        password: '***'
    });

    return api.post<LoginResponse>('/api/v1/auth/login', params, {
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        },
        transformRequest: [(data) => data],
        retry: 3,
        retryDelay: 1000
    });
};

export const getUsers = () => {
    return api.get<User[]>('/api/v1/auth/users');
};

export const createUser = async (data: {
    username: string;
    name: string;
    password: string;
    permissions: string[];
}) => {
    try {
        const response = await api.post<User>('/api/v1/auth/users', data);
        return response;
    } catch (error: any) {
        const errorMessage = error.response?.data?.detail || '创建用户失败';
        throw new Error(errorMessage);
    }
};

export const updateUser = async (userId: number, data: any) => {
    try {
        const response = await api.put<User>(`/api/v1/auth/users/${userId}`, data);
        return response;
    } catch (error: any) {
        const errorMessage = error.response?.data?.detail || '更新用户信息失败';
        throw new Error(errorMessage);
    }
};

export const deleteUser = (id: number) => {
    return api.delete(`/api/v1/auth/users/${id}`);
}; 