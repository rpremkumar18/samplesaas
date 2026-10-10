import { useCallback, useEffect, useState } from 'react';
import { isAxiosError } from 'axios';
import { getRoast, listRoasts } from '../services/roastService';
import type { Roast } from '../types';

export type RoastError = 'not_ready' | 'error' | null;

export function useRoast(submissionId: number) {
  const [roast, setRoast] = useState<Roast | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<RoastError>(null);
  const [attempt, setAttempt] = useState<number>(0);

  useEffect(() => {
    let cancelled = false;
    getRoast(submissionId)
      .then((data) => {
        if (cancelled) return;
        setRoast(data);
        setError(null);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setError(isAxiosError(err) && err.response?.status === 404 ? 'not_ready' : 'error');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [submissionId, attempt]);

  const reload = useCallback((): void => {
    setLoading(true);
    setAttempt((n) => n + 1);
  }, []);

  return { roast, loading, error, reload };
}

export function useRoastHistory(limit = 20) {
  const [roasts, setRoasts] = useState<Roast[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<boolean>(false);
  const [attempt, setAttempt] = useState<number>(0);

  useEffect(() => {
    let cancelled = false;
    listRoasts(0, limit)
      .then((res) => {
        if (cancelled) return;
        setRoasts(res.items);
        setTotal(res.total);
        setError(false);
      })
      .catch(() => {
        if (!cancelled) setError(true);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [limit, attempt]);

  const reload = useCallback((): void => {
    setLoading(true);
    setAttempt((n) => n + 1);
  }, []);

  return { roasts, total, loading, error, reload };
}
