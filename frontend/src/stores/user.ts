import { defineStore } from 'pinia';
import type { User } from '../api/user';
import api from '../api/config';

interface UserState {
    token: string | null;
    user: User | null;
}

export const useUserStore = defineStore('user', {
    state: (): UserState => ({
        token: localStorage.getItem('token'),
        user: JSON.parse(localStorage.getItem('user') || 'null')
    }),

    getters: {
        isLoggedIn: (state) => !!state.token && !!state.user,
        isOwner: (state) => state.user?.is_owner || false,
        hasPermission: (state) => (permission: string) => {
            if (state.user?.is_owner) return true;
            return state.user?.permissions?.includes(permission) || false;
        }
    },

    actions: {
        setToken(token: string) {
            this.token = token;
            localStorage.setItem('token', token);
        },

        setUser(user: User) {
            this.user = user;
            localStorage.setItem('user', JSON.stringify(user));
        },

        logout() {
            this.token = null;
            this.user = null;
            localStorage.removeItem('token');
            localStorage.removeItem('user');
        },

        async restoreUser() {
            if (this.token) {
                try {
                    const response = await api.get('/api/v1/auth/users/me');
                    this.setUser(response);
                    return response;
                } catch (error) {
                    this.logout();
                    throw error;
                }
            }
            return null;
        }
    }
}); 