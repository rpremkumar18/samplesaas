import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react';
import { ACCESS_TOKEN_KEY, clearTokens } from '../services/api';
import { fetchCurrentUser, loginRequest, logoutRequest, registerRequest } from '../services/authService';
import type { RegisterRequest, User } from '../types';
import { AuthContext, type AuthContextValue } from './authContextValue';

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(() => localStorage.getItem(ACCESS_TOKEN_KEY) !== null);

  const refreshUser = useCallback(async (): Promise<void> => {
    if (!localStorage.getItem(ACCESS_TOKEN_KEY)) {
      setUser(null);
      return;
    }
    try {
      setUser(await fetchCurrentUser());
    } catch {
      clearTokens();
      setUser(null);
    }
  }, []);

  useEffect(() => {
    if (!localStorage.getItem(ACCESS_TOKEN_KEY)) return;
    let active = true;
    fetchCurrentUser()
      .then((u) => {
        if (active) setUser(u);
      })
      .catch(() => {
        clearTokens();
        if (active) setUser(null);
      })
      .finally(() => {
        if (active) setIsLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const login = useCallback(async (email: string, password: string): Promise<void> => {
    await loginRequest({ email, password });
    setUser(await fetchCurrentUser());
  }, []);

  const register = useCallback(
    async (payload: RegisterRequest): Promise<void> => {
      await registerRequest(payload);
      await login(payload.email, payload.password);
    },
    [login],
  );

  const logout = useCallback(async (): Promise<void> => {
    try {
      await logoutRequest();
    } catch {
      clearTokens();
    }
    setUser(null);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({ user, isLoading, login, register, logout, refreshUser }),
    [user, isLoading, login, register, logout, refreshUser],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
