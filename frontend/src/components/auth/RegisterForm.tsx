import { useState, type FormEvent } from 'react';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
import { Stack, Text } from '@chakra-ui/react';
import { AnimatedInput } from '../ui/AnimatedInput';
import { GradientButton } from '../ui/GradientButton';
import { GoogleLoginButton } from './GoogleLoginButton';
import { useAuth } from '../../hooks/useAuth';
import { getErrorMessage } from '../../services/authService';

interface FormErrors {
  fullName?: string;
  email?: string;
  password?: string;
  confirm?: string;
}

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function RegisterForm() {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [errors, setErrors] = useState<FormErrors>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const onSubmit = async (e: FormEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();
    const next: FormErrors = {};
    if (!fullName.trim()) next.fullName = 'Full name is required';
    if (!EMAIL_RE.test(email)) next.email = 'Enter a valid email address';
    if (password.length < 8) next.password = 'Password must be at least 8 characters';
    else if (!/[A-Za-z]/.test(password) || !/\d/.test(password)) next.password = 'Use both letters and numbers';
    if (confirm !== password) next.confirm = 'Passwords do not match';
    setErrors(next);
    setFormError(null);
    if (Object.keys(next).length > 0) return;

    setSubmitting(true);
    try {
      await register({ email, password, full_name: fullName.trim() });
      navigate('/dashboard', { replace: true });
    } catch (err) {
      setFormError(getErrorMessage(err, 'Registration failed. Please try again.'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={(e) => void onSubmit(e)} noValidate>
      <Stack gap={4}>
        <AnimatedInput label="Full name" autoComplete="name" value={fullName} error={errors.fullName} onChange={(e) => setFullName(e.target.value)} />
        <AnimatedInput label="Email" type="email" autoComplete="email" value={email} error={errors.email} onChange={(e) => setEmail(e.target.value)} />
        <AnimatedInput label="Password" type="password" autoComplete="new-password" value={password} error={errors.password} onChange={(e) => setPassword(e.target.value)} />
        <AnimatedInput label="Confirm password" type="password" autoComplete="new-password" value={confirm} error={errors.confirm} onChange={(e) => setConfirm(e.target.value)} />
        {formError ? <Text role="alert" color="red.500" fontSize="sm">{formError}</Text> : null}
        <GradientButton type="submit" disabled={submitting} opacity={submitting ? 0.7 : 1}>
          {submitting ? 'Creating account...' : 'Create account'}
        </GradientButton>
        <Text textAlign="center" color="gray.500" fontSize="sm">or</Text>
        <GoogleLoginButton label="Sign up with Google" />
        <Text textAlign="center" fontSize="sm">
          Already have an account?{' '}
          <RouterLink to="/login"><Text as="span" color="purple.600" fontWeight="semibold">Sign in</Text></RouterLink>
        </Text>
      </Stack>
    </form>
  );
}
