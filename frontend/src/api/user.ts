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

export const createUser = (data: {
    username: string;
    name: string;
    password: string;
    permissions: string[];
}) => {
    return api.post<User>('/api/v1/auth/users', data);
};

export const updateUser = (id: number, data: {
    name?: string;
    permissions?: string[];
    password?: string;
}) => {
    return api.put<User>(`/api/v1/auth/users/${id}`, data);
};

export const deleteUser = (id: number) => {
    return api.delete(`/api/v1/auth/users/${id}`);
}; 