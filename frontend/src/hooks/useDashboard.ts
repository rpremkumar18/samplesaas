import { useCallback, useEffect, useState } from 'react';
import api from '../services/api';
import type { PaginatedResponse, Roast, Submission } from '../types';

export interface DashboardData {
  totalSubmissions: number;
  totalRoasts: number;
  averageScore: number | null;
  bestScore: number | null;
  recent: Roast[];
  trend: Roast[];
}

interface UseDashboardResult {
  data: DashboardData | null;
  loading: boolean;
  error: string | null;
  reload: () => void;
}

function buildData(roasts: PaginatedResponse<Roast>, submissionsTotal: number): DashboardData {
  const items = roasts.items;
  const scores = items.map((r) => r.score);
  const byDateDesc = [...items].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
  );
  return {
    totalSubmissions: submissionsTotal,
    totalRoasts: roasts.total,
    averageScore: scores.length ? scores.reduce((a, b) => a + b, 0) / scores.length : null,
    bestScore: scores.length ? Math.max(...scores) : null,
    recent: byDateDesc.slice(0, 5),
    trend: [...byDateDesc].reverse(),
  };
}

export function useDashboard(): UseDashboardResult {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [nonce, setNonce] = useState<number>(0);

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      api.get<PaginatedResponse<Roast>>('/roasts', { params: { skip: 0, limit: 50 } }),
      api.get<PaginatedResponse<Submission>>('/submissions', { params: { skip: 0, limit: 1 } }),
    ])
      .then(([roasts, subs]) => {
        if (!cancelled) setData(buildData(roasts.data, subs.data.total));
      })
      .catch(() => {
        if (!cancelled) setError('Could not load your dashboard. Please try again.');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [nonce]);

  const reload = useCallback(() => {
    setLoading(true);
    setError(null);
    setNonce((n) => n + 1);
  }, []);
  return { data, loading, error, reload };
}
