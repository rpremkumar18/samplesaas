import { useEffect, useState } from 'react';
import { fetchMyRepos } from '../services/repoService';
import { extractErrorMessage } from '../services/submissionService';
import type { GitHubRepo } from '../types';

interface MyReposState {
  repos: GitHubRepo[];
  loading: boolean;
  error: string | null;
}

/** Load the signed-in user's public GitHub repos once (skipped when `enabled` is false). */
export function useMyRepos(enabled: boolean): MyReposState {
  const [state, setState] = useState<MyReposState>({ repos: [], loading: enabled, error: null });

  useEffect(() => {
    if (!enabled) return;
    let cancelled = false;
    fetchMyRepos()
      .then((repos) => {
        if (!cancelled) setState({ repos, loading: false, error: null });
      })
      .catch((e: unknown) => {
        if (!cancelled) {
          setState({ repos: [], loading: false, error: extractErrorMessage(e, 'Could not load your repositories.') });
        }
      });
    return () => {
      cancelled = true;
    };
  }, [enabled]);

  return state;
}
