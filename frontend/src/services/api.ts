import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios';
import type { TokenPair } from '../types';

const API_URL: string = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';
const BASE_URL = `${API_URL}/api/v1`;

export const ACCESS_TOKEN_KEY = 'access_token';
export const REFRESH_TOKEN_KEY = 'refresh_token';

export function storeTokens(tokens: Pick<TokenPair, 'access_token' | 'refresh_token'>): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token);
  localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
}

export function clearTokens(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

interface RetriableConfig extends InternalAxiosRequestConfig {
  _retry?: boolean;
}

const api = axios.create({ baseURL: BASE_URL });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem(ACCESS_TOKEN_KEY);
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

let refreshPromise: Promise<TokenPair> | null = null;

async function refreshTokens(): Promise<TokenPair> {
  const refresh = localStorage.getItem(REFRESH_TOKEN_KEY);
  if (!refresh) throw new Error('No refresh token');
  const { data } = await axios.post<TokenPair>(`${BASE_URL}/auth/refresh`, { refresh_token: refresh });
  storeTokens(data);
  return data;
}

api.interceptors.response.use(
  (res) => res,
  async (error: AxiosError) => {
    const original = error.config as RetriableConfig | undefined;
    const isAuthCall = original?.url?.includes('/auth/login') || original?.url?.includes('/auth/refresh');
    if (error.response?.status === 401 && original && !original._retry && !isAuthCall) {
      original._retry = true;
      try {
        refreshPromise ??= refreshTokens().finally(() => {
          refreshPromise = null;
        });
        await refreshPromise;
        return api(original);
      } catch {
        clearTokens();
        window.location.assign('/login');
      }
    }
    return Promise.reject(error);
  },
);

export default api;
