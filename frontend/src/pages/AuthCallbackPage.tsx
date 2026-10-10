import { useEffect, useRef, useState } from 'react';
import { Navigate, useNavigate } from 'react-router-dom';
import { Center, Spinner, Stack, Text } from '@chakra-ui/react';
import { storeTokens } from '../services/api';
import { useAuth } from '../hooks/useAuth';

interface FragmentTokens {
  accessToken: string;
  refreshToken: string;
}

/** Read tokens from the URL fragment and immediately scrub it from the address bar/history. */
function consumeFragment(): FragmentTokens | null {
  const hash = window.location.hash.replace(/^#/, '');
  window.history.replaceState(null, '', window.location.pathname);
  const params = new URLSearchParams(hash);
  const accessToken = params.get('access_token');
  const refreshToken = params.get('refresh_token');
  return accessToken && refreshToken ? { accessToken, refreshToken } : null;
}

export default function AuthCallbackPage() {
  const navigate = useNavigate();
  const { refreshUser } = useAuth();
  const [failed, setFailed] = useState(false);
  const started = useRef(false);

  useEffect(() => {
    if (started.current) return;
    started.current = true;
    const tokens = consumeFragment();
    if (!tokens) {
      navigate('/login', { replace: true });
      return;
    }
    storeTokens({ access_token: tokens.accessToken, refresh_token: tokens.refreshToken });
    refreshUser()
      .then(() => navigate('/dashboard', { replace: true }))
      .catch(() => setFailed(true));
  }, [refreshUser, navigate]);

  if (failed) return <Navigate to="/login" replace />;

  return (
    <Center minH="100vh">
      <Stack align="center" gap={3}>
        <Spinner size="xl" color={{ base: 'purple.600', _dark: 'purple.300' }} />
        <Text color="fg.muted">Signing you in...</Text>
      </Stack>
    </Center>
  );
}
