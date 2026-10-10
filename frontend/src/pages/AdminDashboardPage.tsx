import { Link as RouterLink } from 'react-router-dom';
import { Alert, Button, Heading, HStack, Spinner, Stack } from '@chakra-ui/react';
import { PageWrapper } from '../components/layout/PageWrapper';
import { AdminStats } from '../components/admin/AdminStats';
import { useAdminStats } from '../hooks/useAdmin';

export default function AdminDashboardPage() {
  const { data, loading, error, reload } = useAdminStats();

  return (
    <PageWrapper>
      <Stack gap={6} maxW="6xl" mx="auto">
        <HStack justify="space-between" wrap="wrap">
          <Heading size="2xl">Admin Dashboard</Heading>
          <HStack>
            <Button asChild variant="outline">
              <RouterLink to="/admin/users">Manage users</RouterLink>
            </Button>
            <Button asChild variant="outline">
              <RouterLink to="/admin/submissions">All submissions</RouterLink>
            </Button>
          </HStack>
        </HStack>
        {loading ? <Spinner alignSelf="center" /> : null}
        {error ? (
          <Alert.Root status="error">
            <Alert.Indicator />
            <Alert.Title>{error}</Alert.Title>
            <Button size="xs" ml="auto" onClick={reload}>
              Retry
            </Button>
          </Alert.Root>
        ) : null}
        {data ? <AdminStats stats={data} /> : null}
      </Stack>
    </PageWrapper>
  );
}
