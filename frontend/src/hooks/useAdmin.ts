import { useCallback, useEffect, useState } from 'react';
import {
  getAdminStats,
  getErrorMessage,
  listAdminSubmissions,
  listAdminUsers,
  updateAdminUser,
  type SubmissionListParams,
  type UserListParams,
} from '../services/adminService';
import type {
  AdminListResponse,
  AdminStatsData,
  AdminSubmission,
  AdminUser,
  AdminUserUpdate,
} from '../types';

interface AsyncState<T> {
  data: T;
  loading: boolean;
  error: string | null;
}

interface Settled<T> {
  key: string;
  data: T | null;
  error: string | null;
}

interface Fetched<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  reload: () => void;
  setData: (updater: (prev: T) => T) => void;
}

/** Runs `fetcher` whenever `key` changes; loading is derived (no sync setState in the effect). */
function useFetched<T>(key: string, fetcher: () => Promise<T>, failure: string): Fetched<T> {
  const [tick, setTick] = useState(0);
  const [settled, setSettled] = useState<Settled<T> | null>(null);
  const fullKey = `${key}#${tick}`;

  useEffect(() => {
    let active = true;
    fetcher()
      .then((data) => {
        if (active) setSettled({ key: fullKey, data, error: null });
      })
      .catch((e: unknown) => {
        if (active) setSettled({ key: fullKey, data: null, error: getErrorMessage(e, failure) });
      });
    return () => {
      active = false;
    };
    // fetcher closes over the params encoded in `key`
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fullKey]);

  const reload = useCallback(() => setTick((t) => t + 1), []);
  const setData = useCallback((updater: (prev: T) => T) => {
    setSettled((s) => (s && s.data !== null ? { ...s, data: updater(s.data) } : s));
  }, []);

  const loading = settled === null || settled.key !== fullKey;
  return {
    data: settled?.data ?? null,
    loading,
    error: loading ? null : (settled?.error ?? null),
    reload,
    setData,
  };
}

export function useAdminStats(): AsyncState<AdminStatsData | null> & { reload: () => void } {
  const { data, loading, error, reload } = useFetched('stats', getAdminStats, 'Failed to load stats');
  return { data, loading, error, reload };
}

interface UsersResult extends AsyncState<AdminUser[]> {
  total: number;
  reload: () => void;
  updateUser: (id: number, update: AdminUserUpdate) => Promise<string | null>;
}

export function useAdminUsers(params: UserListParams): UsersResult {
  const { skip, limit, search } = params;
  const { data, loading, error, reload, setData } = useFetched<AdminListResponse<AdminUser>>(
    `users:${skip}:${limit}:${search ?? ''}`,
    () => listAdminUsers({ skip, limit, search }),
    'Failed to load users',
  );

  /** Returns an error message, or null on success. */
  const updateUser = useCallback(
    async (id: number, update: AdminUserUpdate): Promise<string | null> => {
      try {
        const updated = await updateAdminUser(id, update);
        setData((prev) => ({ ...prev, items: prev.items.map((u) => (u.id === id ? updated : u)) }));
        return null;
      } catch (e: unknown) {
        return getErrorMessage(e, 'Failed to update user');
      }
    },
    [setData],
  );

  return { data: data?.items ?? [], total: data?.total ?? 0, loading, error, reload, updateUser };
}

interface SubmissionsResult extends AsyncState<AdminSubmission[]> {
  total: number;
  reload: () => void;
}

export function useAdminSubmissions(params: SubmissionListParams): SubmissionsResult {
  const { skip, limit, status, user_id } = params;
  const { data, loading, error, reload } = useFetched<AdminListResponse<AdminSubmission>>(
    `subs:${skip}:${limit}:${status ?? ''}:${user_id ?? ''}`,
    () => listAdminSubmissions({ skip, limit, status, user_id }),
    'Failed to load submissions',
  );
  return { data: data?.items ?? [], total: data?.total ?? 0, loading, error, reload };
}
