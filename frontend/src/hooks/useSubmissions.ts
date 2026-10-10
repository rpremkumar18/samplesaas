import { useCallback, useEffect, useState } from 'react';
import { deleteSubmission, extractErrorMessage, listSubmissions } from '../services/submissionService';
import type { Submission } from '../types';

interface UseSubmissionsResult {
  items: Submission[];
  total: number;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  remove: (id: number) => Promise<void>;
}

export function useSubmissions(): UseSubmissionsResult {
  const [items, setItems] = useState<Submission[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async (): Promise<void> => {
    try {
      const res = await listSubmissions(0, 100);
      setItems(res.items);
      setTotal(res.total);
      setError(null);
    } catch (e: unknown) {
      setError(extractErrorMessage(e, 'Could not load submissions.'));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let active = true;
    listSubmissions(0, 100)
      .then((res) => {
        if (!active) return;
        setItems(res.items);
        setTotal(res.total);
        setError(null);
      })
      .catch((e: unknown) => {
        if (active) setError(extractErrorMessage(e, 'Could not load submissions.'));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const remove = useCallback(async (id: number): Promise<void> => {
    await deleteSubmission(id);
    setItems((prev) => prev.filter((s) => s.id !== id));
    setTotal((t) => Math.max(0, t - 1));
  }, []);

  return { items, total, loading, error, refresh, remove };
}
