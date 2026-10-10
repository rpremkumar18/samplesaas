import { useCallback, useEffect, useState } from 'react';
import { extractErrorMessage, getSubmission, retrySubmission } from '../services/submissionService';
import type { Submission, SubmissionStatus } from '../types';

export const POLL_INITIAL_MS = 3000;
export const POLL_MAX_MS = 15000;
export const POLL_BACKOFF_FACTOR = 1.5;
export const POLL_GIVE_UP_MS = 10 * 60 * 1000;
const ACTIVE: SubmissionStatus[] = ['pending', 'fetching', 'analyzing'];

export function isActiveStatus(status: SubmissionStatus): boolean {
  return ACTIVE.includes(status);
}

interface UseSubmissionPollingResult {
  submission: Submission | null;
  loading: boolean;
  error: string | null;
  retrying: boolean;
  /** True once polling gave up after POLL_GIVE_UP_MS while the job was still active. */
  timedOut: boolean;
  /** Fetch now and restart polling (clears the timed-out state). */
  refresh: () => void;
  retry: () => Promise<void>;
}

export function useSubmissionPolling(id: number): UseSubmissionPollingResult {
  const [submission, setSubmission] = useState<Submission | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [retrying, setRetrying] = useState(false);

  const [timedOut, setTimedOut] = useState(false);
  const [pollKey, setPollKey] = useState(0);

  const status = submission?.status;
  const shouldPoll = status === undefined || isActiveStatus(status);

  useEffect(() => {
    if (!Number.isFinite(id) || !shouldPoll) return undefined;
    let cancelled = false;
    let timer: number | null = null;
    let waitingForVisible = false;
    let delay = POLL_INITIAL_MS;
    const startedAt = Date.now();

    const schedule = (): void => {
      timer = window.setTimeout(() => void tick(), delay);
      delay = Math.min(Math.round(delay * POLL_BACKOFF_FACTOR), POLL_MAX_MS);
    };

    const tick = async (): Promise<void> => {
      timer = null;
      if (cancelled) return;
      if (Date.now() - startedAt >= POLL_GIVE_UP_MS) {
        setTimedOut(true);
        return;
      }
      if (document.hidden) {
        waitingForVisible = true;
        return;
      }
      try {
        const data = await getSubmission(id);
        if (cancelled) return;
        setSubmission(data);
        setError(null);
        if (isActiveStatus(data.status)) schedule();
      } catch (e: unknown) {
        if (cancelled) return;
        setError(extractErrorMessage(e, 'Could not load submission.'));
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    const onVisibility = (): void => {
      if (document.hidden || !waitingForVisible || cancelled) return;
      waitingForVisible = false;
      delay = POLL_INITIAL_MS;
      void tick();
    };

    document.addEventListener('visibilitychange', onVisibility);
    void tick();
    return () => {
      cancelled = true;
      document.removeEventListener('visibilitychange', onVisibility);
      if (timer !== null) window.clearTimeout(timer);
    };
  }, [id, shouldPoll, pollKey]);

  const refresh = useCallback((): void => {
    setTimedOut(false);
    setPollKey((k) => k + 1);
  }, []);

  const retry = useCallback(async (): Promise<void> => {
    setRetrying(true);
    try {
      const data = await retrySubmission(id);
      setSubmission(data);
      setError(null);
      setTimedOut(false);
      setPollKey((k) => k + 1);
    } catch (e: unknown) {
      setError(extractErrorMessage(e, 'Retry failed.'));
    } finally {
      setRetrying(false);
    }
  }, [id]);

  return { submission, loading, error: Number.isFinite(id) ? error : 'Invalid submission id.', retrying, timedOut, refresh, retry };
}
