import { useState, type FormEvent } from 'react';
import { Link as RouterLink, useLocation, useNavigate, useSearchParams } from 'react-router-dom';
import { Box, Stack, Text } from '@chakra-ui/react';
import { AnimatedInput } from '../ui/AnimatedInput';
import { GradientButton } from '../ui/GradientButton';
import { GitHubLoginButton } from './GitHubLoginButton';
import { useAuth } from '../../hooks/useAuth';
import { getErrorMessage } from '../../services/authService';

interface LocationState {
  from?: string;
}

interface LoginErrors {
  email?: string;
  password?: string;
}

const OAUTH_ERROR_MESSAGES: Record<string, string> = {
  access_denied: 'GitHub sign-in was cancelled. Please try again.',
  invalid_state: 'Your sign-in session expired or was invalid. Please try again.',
  email_unverified: 'Your GitHub email address is not verified, so we could not sign you in.',
  github_failed: 'GitHub sign-in failed. Please try again.',
  account_unavailable: 'This account cannot sign in right now.',
};

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function LoginForm() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const oauthCode = searchParams.get('error');
  const oauthError = oauthCode ? (OAUTH_ERROR_MESSAGES[oauthCode] ?? null) : null;
  const from = (location.state as LocationState | null)?.from ?? '/dashboard';

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState<LoginErrors>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const onSubmit = async (e: FormEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();
    const next: LoginErrors = {};
    if (!EMAIL_RE.test(email)) next.email = 'Enter a valid email address';
    if (!password) next.password = 'Password is required';
    setErrors(next);
    setFormError(null);
    if (Object.keys(next).length > 0) return;

    setSubmitting(true);
    try {
      await login(email, password);
      navigate(from, { replace: true });
    } catch (err) {
      setFormError(getErrorMessage(err, 'Login failed. Check your email and password.'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={(e) => void onSubmit(e)} noValidate>
      <Stack gap={4}>
        <AnimatedInput label="Email" type="email" autoComplete="email" value={email} error={errors.email} onChange={(e) => setEmail(e.target.value)} />
        <AnimatedInput label="Password" type="password" autoComplete="current-password" value={password} error={errors.password} onChange={(e) => setPassword(e.target.value)} />
        <Box textAlign="right">
          <RouterLink to="/forgot-password">
            <Text as="span" fontSize="sm" color={{ base: 'purple.600', _dark: 'purple.300' }}>Forgot password?</Text>
          </RouterLink>
        </Box>
        {oauthError && !formError ? <Text role="alert" color="fg.error" fontSize="sm">{oauthError}</Text> : null}
        {formError ? <Text role="alert" color="fg.error" fontSize="sm">{formError}</Text> : null}
        <GradientButton type="submit" disabled={submitting} opacity={submitting ? 0.7 : 1}>
          {submitting ? 'Signing in...' : 'Sign in'}
        </GradientButton>
        <Text textAlign="center" color="fg.muted" fontSize="sm">or</Text>
        <GitHubLoginButton />
        <Text textAlign="center" fontSize="sm">
          New here?{' '}
          <RouterLink to="/register"><Text as="span" color={{ base: 'purple.600', _dark: 'purple.300' }} fontWeight="semibold">Create an account</Text></RouterLink>
        </Text>
      </Stack>
    </form>
  );
}
