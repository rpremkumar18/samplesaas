import { Center, Heading, Text } from '@chakra-ui/react';
import { Navigate } from 'react-router-dom';
import { MeshBackground } from '../components/layout/MeshBackground';
import { PageWrapper } from '../components/layout/PageWrapper';
import { GlassCard } from '../components/ui/GlassCard';
import { LoginForm } from '../components/auth/LoginForm';
import { useAuth } from '../hooks/useAuth';

export default function LoginPage() {
  const { user, isLoading } = useAuth();
  if (!isLoading && user) return <Navigate to="/dashboard" replace />;
  return (
    <PageWrapper>
      <MeshBackground />
      <Center minH="80vh">
        <GlassCard w="full" maxW="md">
          <Heading size="2xl" mb={1}>Welcome back</Heading>
          <Text color="fg.muted" mb={6}>Sign in to get your assignment roasted.</Text>
          <LoginForm />
        </GlassCard>
      </Center>
    </PageWrapper>
  );
}
