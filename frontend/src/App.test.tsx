import { render, screen } from '@testing-library/react';
import { ChakraProvider, defaultSystem } from '@chakra-ui/react';
import { vi } from 'vitest';
import App from './App';
import { useAuth } from './hooks/useAuth';
import { makeAuth, makeUser } from './test/utils';

vi.mock('./hooks/useAuth', () => ({ useAuth: vi.fn() }));
vi.mock('./hooks/useDashboard', () => ({
  useDashboard: () => ({ data: null, loading: true, error: null, reload: vi.fn() }),
}));

const mockedUseAuth = vi.mocked(useAuth);

function renderApp(path: string) {
  window.history.pushState({}, '', path);
  return render(
    <ChakraProvider value={defaultSystem}>
      <App />
    </ChakraProvider>,
  );
}

describe('App', () => {
  it('renders the dashboard for a logged-in user', async () => {
    mockedUseAuth.mockReturnValue(makeAuth({ user: makeUser() }));
    renderApp('/');
    expect(await screen.findByRole('heading', { name: 'Dashboard' })).toBeInTheDocument();
    expect(window.location.pathname).toBe('/dashboard');
  });

  it('redirects an anonymous visitor to the login page', async () => {
    mockedUseAuth.mockReturnValue(makeAuth({ user: null }));
    renderApp('/dashboard');
    expect(await screen.findByRole('button', { name: 'Sign in' })).toBeInTheDocument();
    expect(window.location.pathname).toBe('/login');
  });

  it('shows the not-found page for unknown routes', async () => {
    mockedUseAuth.mockReturnValue(makeAuth({ user: makeUser() }));
    renderApp('/definitely/not/a/route');
    expect(await screen.findByRole('heading', { name: 'NotFoundPage' })).toBeInTheDocument();
  });
});
