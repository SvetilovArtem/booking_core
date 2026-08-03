import { create } from 'zustand';

interface AuthStore {
  token: string | null;
  expiresAt: number | null;  // Timestamp истечения
  setToken: (token: string, expiresIn: number) => void;
  logout: () => void;
  isAuthenticated: () => boolean;
  isTokenExpired: () => boolean;
}

export const useAuthStore = create<AuthStore>((set, get) => ({
  token: localStorage.getItem('token'),
  expiresAt: localStorage.getItem('expiresAt') ? parseInt(localStorage.getItem('expiresAt')!) : null,

  setToken: (token, expiresIn) => {
    const expiresAt = Date.now() + expiresIn * 1000;
    localStorage.setItem('token', token);
    localStorage.setItem('expiresAt', expiresAt.toString());
    set({ token, expiresAt });
  },

  logout: () => {
    localStorage.removeItem('token');
    localStorage.removeItem('expiresAt');
    set({ token: null, expiresAt: null });
  },

  isAuthenticated: () => {
    const { token, expiresAt } = get();
    if (!token || !expiresAt) return false;
    return Date.now() < expiresAt;  // Токен существует и не истек
  },

  isTokenExpired: () => {
    const { expiresAt } = get();
    if (!expiresAt) return true;
    return Date.now() >= expiresAt;
  },
}));