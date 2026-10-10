import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Route, Routes } from 'react-router-dom';
import { vi } from 'vitest';
import AuthCallbackPage from '../pages/AuthCallbackPage';
import { storeTokens } from '../services/api';
import { LoginForm } from '../components/auth/LoginForm';
import { RegisterForm } from '../components/auth/RegisterForm';
import { ProtectedRoute } from '../components/ProtectedRoute';
import { useAuth } from '../hooks/useAuth';
import { makeAuth, makeUser, renderWithProviders } from '../test/utils';

vi.mock('../hooks/useAuth', () => ({ useAuth: vi.fn() }));
vi.mock('../services/api', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../services/api')>()),
  storeTokens: vi.fn(),
}));
const mockedUseAuth = vi.mocked(useAuth);

function routes() {
  const Guard = ProtectedRoute;
  return (
    <Routes>
      <Route path="/login" element={<div>login-page</div>} />
      <Route path="/dashboard" element={<div>dashboard-page</div>} />
      <Route
        path="/secret"
        element={
          <Guard>
            <div>secret-content</div>
          </Guard>
        }
      />
    </Routes>
  );
}

describe('LoginForm', () => {
  it('shows validation errors and does not call login', async () => {
    const login = vi.fn();
    mockedUseAuth.mockReturnValue(makeAuth({ login }));
    renderWithProviders(<LoginForm />);
    await userEvent.type(screen.getByLabelText('Email'), 'not-an-email');
    await userEvent.click(screen.getByRole('button', { name: 'Sign in' }));
    expect(await screen.findByText('Enter a valid email address')).toBeInTheDocument();
    expect(screen.getByText('Password is required')).toBeInTheDocument();
    expect(login).not.toHaveBeenCalled();
  });

  it('submits credentials and navigates to the dashboard', async () => {
    const login = vi.fn().mockResolvedValue(undefined);
    mockedUseAuth.mockReturnValue(makeAuth({ login }));
    renderWithProviders(
      <Routes>
        <Route path="/login" element={<LoginForm />} />
        <Route path="/dashboard" element={<div>dashboard-page</div>} />
      </Routes>,
      { route: '/login' },
    );
    await userEvent.type(screen.getByLabelText('Email'), 'a@b.co');
    await userEvent.type(screen.getByLabelText('Password'), 'secret123');
    await userEvent.click(screen.getByRole('button', { name: 'Sign in' }));
    await waitFor(() => expect(login).toHaveBeenCalledWith('a@b.co', 'secret123'));
    expect(await screen.findByText('dashboard-page')).toBeInTheDocument();
  });

  it('shows an error when login fails', async () => {
    const login = vi.fn().mockRejectedValue(new Error('nope'));
    mockedUseAuth.mockReturnValue(makeAuth({ login }));
    renderWithProviders(<LoginForm />);
    await userEvent.type(screen.getByLabelText('Email'), 'a@b.co');
    await userEvent.type(screen.getByLabelText('Password'), 'x');
    await userEvent.click(screen.getByRole('button', { name: 'Sign in' }));
    expect(await screen.findByRole('alert')).toHaveTextContent(/login failed/i);
  });
});

describe('LoginForm OAuth errors', () => {
  it('shows a friendly message for a known error code', () => {
    mockedUseAuth.mockReturnValue(makeAuth());
    renderWithProviders(<LoginForm />, { route: '/login?error=access_denied' });
    expect(screen.getByRole('alert')).toHaveTextContent(/cancelled/i);
  });

  it('ignores unknown error codes', () => {
    mockedUseAuth.mockReturnValue(makeAuth());
    renderWithProviders(<LoginForm />, { route: '/login?error=<script>' });
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });
});

describe('AuthCallbackPage', () => {
  const callbackRoutes = (
    <Routes>
      <Route path="/auth/callback" element={<AuthCallbackPage />} />
      <Route path="/dashboard" element={<div>dashboard-page</div>} />
      <Route path="/login" element={<div>login-page</div>} />
    </Routes>
  );

  afterEach(() => {
    window.history.replaceState(null, '', '/');
    vi.mocked(storeTokens).mockClear();
  });

  it('strips the fragment, stores tokens and goes to the dashboard', async () => {
    window.history.replaceState(null, '', '/auth/callback#access_token=AAA&refresh_token=RRR');
    const replaceSpy = vi.spyOn(window.history, 'replaceState');
    const refreshUser = vi.fn().mockResolvedValue(undefined);
    mockedUseAuth.mockReturnValue(makeAuth({ refreshUser }));
    renderWithProviders(callbackRoutes, { route: '/auth/callback' });
    expect(replaceSpy).toHaveBeenCalledWith(null, '', '/auth/callback');
    expect(window.location.hash).toBe('');
    expect(storeTokens).toHaveBeenCalledWith({ access_token: 'AAA', refresh_token: 'RRR' });
    expect(await screen.findByText('dashboard-page')).toBeInTheDocument();
    replaceSpy.mockRestore();
  });

  it('goes to /login when /auth/me fails', async () => {
    window.history.replaceState(null, '', '/auth/callback#access_token=AAA&refresh_token=RRR');
    mockedUseAuth.mockReturnValue(makeAuth({ refreshUser: vi.fn().mockRejectedValue(new Error('x')) }));
    renderWithProviders(callbackRoutes, { route: '/auth/callback' });
    expect(await screen.findByText('login-page')).toBeInTheDocument();
  });

  it('goes to /login without tokens in the fragment', async () => {
    window.history.replaceState(null, '', '/auth/callback');
    mockedUseAuth.mockReturnValue(makeAuth());
    renderWithProviders(callbackRoutes, { route: '/auth/callback' });
    expect(await screen.findByText('login-page')).toBeInTheDocument();
    expect(storeTokens).not.toHaveBeenCalled();
  });
});

describe('RegisterForm', () => {
  async function fill(values: { name?: string; email?: string; pw?: string; confirm?: string }) {
    if (values.name) await userEvent.type(screen.getByLabelText('Full name'), values.name);
    if (values.email) await userEvent.type(screen.getByLabelText('Email'), values.email);
    if (values.pw) await userEvent.type(screen.getByLabelText('Password'), values.pw);
    if (values.confirm) await userEvent.type(screen.getByLabelText('Confirm password'), values.confirm);
    await userEvent.click(screen.getByRole('button', { name: 'Create account' }));
  }

  it('validates required fields', async () => {
    const register = vi.fn();
    mockedUseAuth.mockReturnValue(makeAuth({ register }));
    renderWithProviders(<RegisterForm />);
    await fill({});
    expect(await screen.findByText('Full name is required')).toBeInTheDocument();
    expect(screen.getByText('Enter a valid email address')).toBeInTheDocument();
    expect(screen.getByText('Password must be at least 8 characters')).toBeInTheDocument();
    expect(register).not.toHaveBeenCalled();
  });

  it('requires letters and digits and matching confirmation', async () => {
    const register = vi.fn();
    mockedUseAuth.mockReturnValue(makeAuth({ register }));
    renderWithProviders(<RegisterForm />);
    await fill({ name: 'N', email: 'a@b.co', pw: 'onlyletters', confirm: 'different' });
    expect(await screen.findByText('Use both letters and numbers')).toBeInTheDocument();
    expect(screen.getByText('Passwords do not match')).toBeInTheDocument();
    expect(register).not.toHaveBeenCalled();
  });

  it('submits a valid registration', async () => {
    const register = vi.fn().mockResolvedValue(undefined);
    mockedUseAuth.mockReturnValue(makeAuth({ register }));
    renderWithProviders(<RegisterForm />);
    await fill({ name: ' Nia ', email: 'a@b.co', pw: 'password1', confirm: 'password1' });
    await waitFor(() =>
      expect(register).toHaveBeenCalledWith({
        email: 'a@b.co',
        password: 'password1',
        full_name: 'Nia',
      }),
    );
  });

  it('shows a server error', async () => {
    const register = vi.fn().mockRejectedValue(new Error('dup'));
    mockedUseAuth.mockReturnValue(makeAuth({ register }));
    renderWithProviders(<RegisterForm />);
    await fill({ name: 'N', email: 'a@b.co', pw: 'password1', confirm: 'password1' });
    expect(await screen.findByRole('alert')).toHaveTextContent(/registration failed/i);
  });
});

describe('ProtectedRoute', () => {
  it('redirects anonymous users to /login', () => {
    mockedUseAuth.mockReturnValue(makeAuth({ user: null }));
    renderWithProviders(routes(), { route: '/secret' });
    expect(screen.getByText('login-page')).toBeInTheDocument();
    expect(screen.queryByText('secret-content')).not.toBeInTheDocument();
  });

  it('renders children for a logged-in user', () => {
    mockedUseAuth.mockReturnValue(makeAuth({ user: makeUser() }));
    renderWithProviders(routes(), { route: '/secret' });
    expect(screen.getByText('secret-content')).toBeInTheDocument();
  });

  it('renders neither content nor redirect while loading', () => {
    mockedUseAuth.mockReturnValue(makeAuth({ user: null, isLoading: true }));
    renderWithProviders(routes(), { route: '/secret' });
    expect(screen.queryByText('secret-content')).not.toBeInTheDocument();
    expect(screen.queryByText('login-page')).not.toBeInTheDocument();
  });
});
