import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import type { ComponentProps } from 'react';
import { vi } from 'vitest';
import { RepoPicker } from '../components/submissions/RepoPicker';
import type { GitHubRepo } from '../types';
import { renderWithProviders } from '../test/utils';

const repos: GitHubRepo[] = [
  { name: 'todo-app', html_url: 'https://github.com/me/todo-app', description: 'A todo', language: 'TypeScript', pushed_at: null },
  { name: 'calc', html_url: 'https://github.com/me/calc', description: null, language: null, pushed_at: null },
];

function setup(overrides: Partial<ComponentProps<typeof RepoPicker>> = {}) {
  const onSubmit = vi.fn().mockResolvedValue(undefined);
  renderWithProviders(
    <RepoPicker repos={repos} loading={false} error={null} onSubmit={onSubmit} submitting={false} serverError={null} {...overrides} />,
  );
  return onSubmit;
}

describe('RepoPicker', () => {
  it('disables submit until a repo is selected, then submits its URL and title', async () => {
    const onSubmit = setup();
    expect(screen.getByRole('button', { name: 'Select a repository' })).toBeDisabled();
    await userEvent.click(screen.getByRole('button', { name: /todo-app/ }));
    await userEvent.type(screen.getByPlaceholderText(/Week 3/), 'HW 3');
    await userEvent.click(screen.getByRole('button', { name: 'Roast todo-app' }));
    expect(onSubmit).toHaveBeenCalledWith('https://github.com/me/todo-app', 'HW 3');
  });

  it('filters repositories by search text', async () => {
    setup();
    await userEvent.type(screen.getByLabelText('Search repositories'), 'calc');
    expect(screen.queryByRole('button', { name: /todo-app/ })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /calc/ })).toBeInTheDocument();
  });

  it('shows the loading state', () => {
    setup({ loading: true });
    expect(screen.getByLabelText('Loading repositories')).toBeInTheDocument();
  });

  it('shows the error message', () => {
    setup({ error: 'boom' });
    expect(screen.getByText('boom')).toBeInTheDocument();
  });

  it('shows an empty state when the user has no public repos', () => {
    setup({ repos: [] });
    expect(screen.getByText(/No public repositories found/)).toBeInTheDocument();
  });
});
