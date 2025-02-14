import { defineStore } from 'pinia';
import type { User } from '../api/user';

interface UserState {
    token: string | null;
    user: User | null;
}

export const useUserStore = defineStore('user', {
    state: (): UserState => ({
        token: localStorage.getItem('token'),
        user: null
    }),

    getters: {
        isLoggedIn: (state) => !!state.token,
        isOwner: (state) => state.user?.is_owner || false,
        hasPermission: (state) => (permission: string) => {
            if (state.user?.is_owner) return true;
            return state.user?.permissions.includes(permission) || false;
        }
    },

    actions: {
        setToken(token: string) {
            this.token = token;
            localStorage.setItem('token', token);
        },

        setUser(user: User) {
            this.user = user;
        },

        logout() {
            this.token = null;
            this.user = null;
            localStorage.removeItem('token');
        }
    }
}); 