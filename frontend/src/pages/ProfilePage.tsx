import { Badge, Box, Heading, HStack, Text } from '@chakra-ui/react';
import { PageWrapper } from '../components/layout/PageWrapper';
import { GlassCard } from '../components/ui/GlassCard';
import { ProfileForm } from '../components/auth/ProfileForm';
import { useAuth } from '../hooks/useAuth';

export default function ProfilePage() {
  const { user } = useAuth();
  return (
    <PageWrapper>
      <Box maxW="lg" mx="auto">
        <Heading size="2xl" mb={6}>Your profile</Heading>
        <GlassCard>
          <HStack mb={4} gap={2}>
            {user?.is_admin ? <Badge colorPalette="purple">Admin</Badge> : null}
            {user?.oauth_provider ? <Badge colorPalette="blue">{user.oauth_provider}</Badge> : null}
            {user?.is_verified ? <Badge colorPalette="green">Verified</Badge> : null}
          </HStack>
          {user ? <ProfileForm key={user.id} /> : <Text>Loading...</Text>}
        </GlassCard>
      </Box>
    </PageWrapper>
  );
}
