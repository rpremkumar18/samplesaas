import { screen } from '@testing-library/react';
import { vi } from 'vitest';
import { Route, Routes } from 'react-router-dom';
import { ProtectedRoute } from '../components/ProtectedRoute';
import NotFoundPage from '../pages/NotFoundPage';
import { useAuth } from '../hooks/useAuth';
import { makeAuth, makeUser, renderWithProviders } from '../test/utils';

vi.mock('../hooks/useAuth', () => ({ useAuth: vi.fn() }));
const mockedUseAuth = vi.mocked(useAuth);

function renderRoutes(route: string) {
  return renderWithProviders(
    <Routes>
      <Route path="/login" element={<div>login page</div>} />
      <Route path="/dashboard" element={<div>dashboard page</div>} />
      <Route path="/secret" element={<ProtectedRoute><div>secret</div></ProtectedRoute>} />
    </Routes>,
    { route },
  );
}

describe('ProtectedRoute', () => {
  it('redirects anonymous users to login', () => {
    mockedUseAuth.mockReturnValue(makeAuth({ user: null }));
    renderRoutes('/secret');
    expect(screen.getByText('login page')).toBeInTheDocument();
  });

  it('renders children for a signed-in user', () => {
    mockedUseAuth.mockReturnValue(makeAuth({ user: makeUser() }));
    renderRoutes('/secret');
    expect(screen.getByText('secret')).toBeInTheDocument();
  });
});

describe('NotFoundPage', () => {
  it('shows a 404 with a link back to the dashboard', () => {
    renderWithProviders(<NotFoundPage />);
    expect(screen.getByRole('heading', { name: 'Page not found' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Back to dashboard' })).toHaveAttribute('href', '/dashboard');
  });
});
