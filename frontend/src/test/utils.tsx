/* eslint-disable react-refresh/only-export-components */
import type { ReactElement, ReactNode } from 'react';
import { render, type RenderResult } from '@testing-library/react';
import { ChakraProvider, defaultSystem } from '@chakra-ui/react';
import { MemoryRouter, useLocation } from 'react-router-dom';
import type { AuthContextValue } from '../context/authContextValue';
import type { ImprovementTip, Roast, Submission, User } from '../types';

export function makeUser(overrides: Partial<User> = {}): User {
  return {
    id: 1,
    email: 'user@example.com',
    full_name: 'Test User',
    is_active: true,
    is_verified: true,
    oauth_provider: null,
    github_login: null,
    created_at: '2025-01-01T00:00:00Z',
    ...overrides,
  };
}

export function makeAuth(overrides: Partial<AuthContextValue> = {}): AuthContextValue {
  return {
    user: null,
    isLoading: false,
    login: async () => undefined,
    register: async () => undefined,
    logout: async () => undefined,
    refreshUser: async () => undefined,
    ...overrides,
  };
}

export function makeSubmission(overrides: Partial<Submission> = {}): Submission {
  return {
    id: 5,
    user_id: 1,
    repo_url: 'https://github.com/o/r',
    repo_owner: 'o',
    repo_name: 'r',
    assignment_title: 'HW',
    status: 'pending',
    error_message: null,
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
    ...overrides,
  };
}

export function makeTip(overrides: Partial<ImprovementTip> = {}): ImprovementTip {
  return {
    id: 1,
    category: 'bugs',
    title: 'Fix it',
    description: 'Because.',
    file_path: null,
    ...overrides,
  };
}

export function makeRoast(overrides: Partial<Roast> = {}): Roast {
  return {
    id: 1,
    submission_id: 5,
    repo_url: 'https://github.com/o/r',
    assignment_title: 'HW',
    roast_text: 'Roast',
    score: 50,
    summary: 'Sum',
    tips: [],
    created_at: '2025-01-01T00:00:00Z',
    ...overrides,
  };
}

export function LocationProbe() {
  const loc = useLocation();
  return <div data-testid="location">{loc.pathname}</div>;
}

export function renderWithProviders(
  ui: ReactElement,
  { route = '/' }: { route?: string } = {},
): RenderResult {
  const wrap = ({ children }: { children: ReactNode }) => (
    <ChakraProvider value={defaultSystem}>
      <MemoryRouter initialEntries={[route]}>
        {children}
        <LocationProbe />
      </MemoryRouter>
    </ChakraProvider>
  );
  return render(ui, { wrapper: wrap });
}
