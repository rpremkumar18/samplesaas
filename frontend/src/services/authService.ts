import api, { REFRESH_TOKEN_KEY, clearTokens, storeTokens } from './api';
import type { LoginRequest, RegisterRequest, TokenPair, UpdateProfileRequest, User } from '../types';

const API_URL: string = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

export const GOOGLE_LOGIN_URL = `${API_URL}/api/v1/auth/google`;

export async function loginRequest(payload: LoginRequest): Promise<TokenPair> {
  const { data } = await api.post<TokenPair>('/auth/login', payload);
  storeTokens(data);
  return data;
}

export async function registerRequest(payload: RegisterRequest): Promise<User> {
  const { data } = await api.post<User>('/auth/register', payload);
  return data;
}

export async function logoutRequest(): Promise<void> {
  const refresh = localStorage.getItem(REFRESH_TOKEN_KEY);
  try {
    if (refresh) await api.post('/auth/logout', { refresh_token: refresh });
  } finally {
    clearTokens();
  }
}

export async function fetchCurrentUser(): Promise<User> {
  const { data } = await api.get<User>('/auth/me');
  return data;
}

export async function updateProfile(payload: UpdateProfileRequest): Promise<User> {
  const { data } = await api.put<User>('/auth/me', payload);
  return data;
}

interface ApiErrorBody {
  detail?: string | { msg?: string }[];
}

/** Extract a human-friendly message from an axios-style error. */
export function getErrorMessage(error: unknown, fallback = 'Something went wrong. Please try again.'): string {
  if (typeof error === 'object' && error !== null && 'response' in error) {
    const response = (error as { response?: { data?: ApiErrorBody } }).response;
    const detail = response?.data?.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg;
  }
  return fallback;
}
