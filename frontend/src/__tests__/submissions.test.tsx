import { act, renderHook, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi } from 'vitest';
import { RepoUrlForm } from '../components/submissions/RepoUrlForm';
import { StatusBadge } from '../components/submissions/StatusBadge';
import { StatusTracker } from '../components/submissions/StatusTracker';
import { useSubmissionPolling } from '../hooks/useSubmissionPolling';
import { getSubmission, retrySubmission } from '../services/submissionService';
import { makeSubmission, renderWithProviders } from '../test/utils';
import type { SubmissionStatus } from '../types';

vi.mock('../services/submissionService', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/submissionService')>();
  return { ...actual, getSubmission: vi.fn(), retrySubmission: vi.fn() };
});
const mockedGet = vi.mocked(getSubmission);
const mockedRetry = vi.mocked(retrySubmission);

describe('RepoUrlForm', () => {
  const URL_ERROR = 'Enter a URL like https://github.com/owner/repo';

  async function submit(url: string, onSubmit = vi.fn().mockResolvedValue(undefined)) {
    renderWithProviders(<RepoUrlForm onSubmit={onSubmit} submitting={false} serverError={null} />);
    const input = screen.getByPlaceholderText('https://github.com/owner/repo');
    if (url) await userEvent.type(input, url);
    await userEvent.click(screen.getByRole('button', { name: 'Roast my code' }));
    return onSubmit;
  }

  it.each([
    '',
    'http://github.com/o/r',
    'https://gitlab.com/o/r',
    'https://github.com/o',
    'https://github.com/o/r/tree/main',
    'https://github.com/o/r?x=1',
    'https://user@github.com/o/r',
    'github.com/o/r',
    'not a url',
  ])('rejects %j', async (bad) => {
    const onSubmit = await submit(bad);
    expect(await screen.findByText(URL_ERROR)).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it('submits a valid URL with trimmed title', async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    renderWithProviders(<RepoUrlForm onSubmit={onSubmit} submitting={false} serverError={null} />);
    await userEvent.type(screen.getByPlaceholderText('https://github.com/owner/repo'), 'https://github.com/octocat/hello-world');
    await userEvent.type(screen.getByPlaceholderText(/Week 3/), '  HW1  ');
    await userEvent.click(screen.getByRole('button', { name: 'Roast my code' }));
    expect(onSubmit).toHaveBeenCalledWith('https://github.com/octocat/hello-world', 'HW1');
    expect(screen.queryByText(URL_ERROR)).not.toBeInTheDocument();
  });

  it('omits an empty title and shows server errors / disabled state', async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    const { rerender } = renderWithProviders(
      <RepoUrlForm onSubmit={onSubmit} submitting={false} serverError={null} />,
    );
    await userEvent.type(screen.getByPlaceholderText('https://github.com/owner/repo'), 'https://github.com/o/r');
    await userEvent.click(screen.getByRole('button', { name: 'Roast my code' }));
    expect(onSubmit).toHaveBeenCalledWith('https://github.com/o/r', undefined);
    rerender(<RepoUrlForm onSubmit={onSubmit} submitting={true} serverError="Boom from server" />);
    expect(screen.getByText('Boom from server')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Submitting...' })).toBeDisabled();
  });
});

describe('StatusBadge', () => {
  it.each<[SubmissionStatus, string]>([
    ['pending', 'Pending'],
    ['fetching', 'Fetching repo'],
    ['analyzing', 'Analyzing'],
    ['completed', 'Completed'],
    ['failed', 'Failed'],
  ])('renders %s', (status, label) => {
    renderWithProviders(<StatusBadge status={status} />);
    expect(screen.getByText(label)).toBeInTheDocument();
  });
});

describe('StatusTracker', () => {
  it('shows a spinner quip while active and none when completed', () => {
    const { rerender } = renderWithProviders(<StatusTracker status="analyzing" />);
    expect(screen.getByText('Reading your commit messages. Oh dear.')).toBeInTheDocument();
    rerender(<StatusTracker status="completed" />);
    expect(screen.queryByText('Reading your commit messages. Oh dear.')).not.toBeInTheDocument();
    expect(screen.getByText('Roast ready')).toBeInTheDocument();
  });

  it('shows a taking-longer notice with a refresh button when timed out', async () => {
    const onRefresh = vi.fn();
    renderWithProviders(<StatusTracker status="analyzing" timedOut onRefresh={onRefresh} />);
    expect(screen.getByText(/taking longer than expected/)).toBeInTheDocument();
    expect(screen.queryByText('Reading your commit messages. Oh dear.')).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: 'Refresh status' }));
    expect(onRefresh).toHaveBeenCalledTimes(1);
  });

  it('shows no quip when failed', () => {
    renderWithProviders(<StatusTracker status="failed" />);
    expect(screen.queryByText(/Waiting in line/)).not.toBeInTheDocument();
  });
});

describe('useSubmissionPolling', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    mockedGet.mockReset();
    mockedRetry.mockReset();
  });
  afterEach(() => {
    vi.useRealTimers();
  });

  it('keeps polling while active and stops once completed', async () => {
    mockedGet
      .mockResolvedValueOnce(makeSubmission({ status: 'pending' }))
      .mockResolvedValueOnce(makeSubmission({ status: 'analyzing' }))
      .mockResolvedValue(makeSubmission({ status: 'completed' }));
    const { result } = renderHook(() => useSubmissionPolling(5));

    await act(async () => {
      await vi.advanceTimersByTimeAsync(0);
    });
    expect(result.current.submission?.status).toBe('pending');
    await act(async () => {
      await vi.advanceTimersByTimeAsync(3000);
    });
    expect(result.current.submission?.status).toBe('analyzing');
    await act(async () => {
      await vi.advanceTimersByTimeAsync(4500);
    });
    expect(result.current.submission?.status).toBe('completed');
    expect(mockedGet).toHaveBeenCalledTimes(3);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(30_000);
    });
    expect(mockedGet).toHaveBeenCalledTimes(3); // polling stopped
  });

  it('backs off from 3s up to 15s between polls', async () => {
    mockedGet.mockResolvedValue(makeSubmission({ status: 'analyzing' }));
    renderHook(() => useSubmissionPolling(5));
    const flush = async (ms: number) => {
      await act(async () => {
        await vi.advanceTimersByTimeAsync(ms);
      });
    };
    await flush(0);
    expect(mockedGet).toHaveBeenCalledTimes(1);
    await flush(2999);
    expect(mockedGet).toHaveBeenCalledTimes(1);
    await flush(1); // 3s
    expect(mockedGet).toHaveBeenCalledTimes(2);
    await flush(4499);
    expect(mockedGet).toHaveBeenCalledTimes(2);
    await flush(1); // +4.5s
    expect(mockedGet).toHaveBeenCalledTimes(3);
    await flush(60_000); // delays settle at the 15s cap: 6.75s, 10.1s, 15s, 15s, 15s...
    expect(mockedGet.mock.calls.length).toBeLessThanOrEqual(3 + 6);
    const before = mockedGet.mock.calls.length;
    await flush(15_000);
    expect(mockedGet).toHaveBeenCalledTimes(before + 1);
  });

  it('pauses while the document is hidden and resumes on visibility', async () => {
    mockedGet.mockResolvedValue(makeSubmission({ status: 'analyzing' }));
    let hidden = false;
    const spy = vi.spyOn(document, 'hidden', 'get').mockImplementation(() => hidden);
    renderHook(() => useSubmissionPolling(5));
    await act(async () => {
      await vi.advanceTimersByTimeAsync(0);
    });
    expect(mockedGet).toHaveBeenCalledTimes(1);
    hidden = true;
    await act(async () => {
      await vi.advanceTimersByTimeAsync(60_000);
    });
    expect(mockedGet).toHaveBeenCalledTimes(1);
    hidden = false;
    await act(async () => {
      document.dispatchEvent(new Event('visibilitychange'));
      await vi.advanceTimersByTimeAsync(0);
    });
    expect(mockedGet).toHaveBeenCalledTimes(2);
    spy.mockRestore();
  });

  it('gives up after ~10 minutes, then refresh restarts polling', async () => {
    mockedGet.mockResolvedValue(makeSubmission({ status: 'analyzing' }));
    const { result } = renderHook(() => useSubmissionPolling(5));
    await act(async () => {
      await vi.advanceTimersByTimeAsync(10 * 60 * 1000 + 20_000);
    });
    expect(result.current.timedOut).toBe(true);
    const calls = mockedGet.mock.calls.length;
    await act(async () => {
      await vi.advanceTimersByTimeAsync(5 * 60 * 1000);
    });
    expect(mockedGet).toHaveBeenCalledTimes(calls);

    await act(async () => {
      result.current.refresh();
      await vi.advanceTimersByTimeAsync(0);
    });
    expect(result.current.timedOut).toBe(false);
    expect(mockedGet).toHaveBeenCalledTimes(calls + 1);
  });

  it('stops polling on unmount', async () => {
    mockedGet.mockResolvedValue(makeSubmission({ status: 'fetching' }));
    const { unmount } = renderHook(() => useSubmissionPolling(5));
    await act(async () => {
      await vi.advanceTimersByTimeAsync(0);
    });
    unmount();
    await act(async () => {
      await vi.advanceTimersByTimeAsync(20_000);
    });
    expect(mockedGet).toHaveBeenCalledTimes(1);
  });

  it('does not poll when already failed, and retry restarts via service', async () => {
    mockedGet
      .mockResolvedValueOnce(makeSubmission({ status: 'failed', error_message: 'bad' }))
      .mockResolvedValue(makeSubmission({ status: 'pending' }));
    mockedRetry.mockResolvedValue(makeSubmission({ status: 'pending' }));
    const { result } = renderHook(() => useSubmissionPolling(5));
    await act(async () => {
      await vi.advanceTimersByTimeAsync(0);
    });
    expect(result.current.submission?.status).toBe('failed');
    await act(async () => {
      await vi.advanceTimersByTimeAsync(10_000);
    });
    expect(mockedGet).toHaveBeenCalledTimes(1);

    await act(async () => {
      await result.current.retry();
    });
    expect(mockedRetry).toHaveBeenCalledWith(5);
    expect(result.current.submission?.status).toBe('pending');
  });

  it('reports an invalid id without calling the API', async () => {
    const { result } = renderHook(() => useSubmissionPolling(Number.NaN));
    await act(async () => {
      await vi.advanceTimersByTimeAsync(5000);
    });
    expect(result.current.error).toBe('Invalid submission id.');
    expect(mockedGet).not.toHaveBeenCalled();
  });

  it('surfaces load errors', async () => {
    mockedGet.mockRejectedValue(new Error('x'));
    const { result } = renderHook(() => useSubmissionPolling(5));
    await act(async () => {
      await vi.advanceTimersByTimeAsync(0);
    });
    expect(result.current.error).toBe('Could not load submission.');
  });
});
