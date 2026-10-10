import { Center, Heading, Text } from '@chakra-ui/react';
import { Navigate } from 'react-router-dom';
import { MeshBackground } from '../components/layout/MeshBackground';
import { PageWrapper } from '../components/layout/PageWrapper';
import { GlassCard } from '../components/ui/GlassCard';
import { RegisterForm } from '../components/auth/RegisterForm';
import { useAuth } from '../hooks/useAuth';

export default function RegisterPage() {
  const { user, isLoading } = useAuth();
  if (!isLoading && user) return <Navigate to="/dashboard" replace />;
  return (
    <PageWrapper>
      <MeshBackground />
      <Center minH="80vh">
        <GlassCard w="full" maxW="md">
          <Heading size="2xl" mb={1}>Create your account</Heading>
          <Text color="gray.600" mb={6}>Join Assignment Roaster and level up your code.</Text>
          <RegisterForm />
        </GlassCard>
      </Center>
    </PageWrapper>
  );
}
