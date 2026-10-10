import { useState } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import { Alert, Box, Button, Heading, HStack, Input, NativeSelect, Spinner, Stack, Text } from '@chakra-ui/react';
import { PageWrapper } from '../components/layout/PageWrapper';
import { AdminSubmissionTable } from '../components/admin/AdminSubmissionTable';
import { Pagination } from '../components/admin/Pagination';
import { RoastDrawer } from '../components/admin/RoastDrawer';
import { useAdminSubmissions } from '../hooks/useAdmin';
import type { AdminSubmission, SubmissionStatus } from '../types';

const PAGE_SIZE = 20;
const STATUSES: SubmissionStatus[] = ['pending', 'fetching', 'analyzing', 'completed', 'failed'];

function isStatus(value: string): value is SubmissionStatus {
  return (STATUSES as string[]).includes(value);
}

export default function AdminSubmissionsPage() {
  const [skip, setSkip] = useState(0);
  const [status, setStatus] = useState<SubmissionStatus | undefined>(undefined);
  const [userIdInput, setUserIdInput] = useState('');
  const [selected, setSelected] = useState<AdminSubmission | null>(null);

  const parsedUserId = Number.parseInt(userIdInput, 10);
  const userId = Number.isNaN(parsedUserId) ? undefined : parsedUserId;

  const { data, total, loading, error, reload } = useAdminSubmissions({
    skip,
    limit: PAGE_SIZE,
    status,
    user_id: userId,
  });

  return (
    <PageWrapper>
      <Stack gap={6} maxW="6xl" mx="auto">
        <HStack justify="space-between" wrap="wrap">
          <Heading size="2xl">All Submissions</Heading>
          <Button asChild variant="outline">
            <RouterLink to="/admin">Back to dashboard</RouterLink>
          </Button>
        </HStack>
        <HStack wrap="wrap">
          <NativeSelect.Root maxW="xs">
            <NativeSelect.Field
              aria-label="Filter by status"
              value={status ?? ''}
              onChange={(e) => {
                setStatus(isStatus(e.target.value) ? e.target.value : undefined);
                setSkip(0);
              }}
            >
              <option value="">All statuses</option>
              {STATUSES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </NativeSelect.Field>
            <NativeSelect.Indicator />
          </NativeSelect.Root>
          <Input
            aria-label="Filter by user ID"
            placeholder="User ID"
            type="number"
            min={1}
            maxW="xs"
            value={userIdInput}
            onChange={(e) => {
              setUserIdInput(e.target.value);
              setSkip(0);
            }}
          />
        </HStack>
        {error ? (
          <Alert.Root status="error">
            <Alert.Indicator />
            <Alert.Title>{error}</Alert.Title>
            <Button size="xs" ml="auto" onClick={reload}>
              Retry
            </Button>
          </Alert.Root>
        ) : null}
        {loading ? <Spinner alignSelf="center" /> : null}
        {!loading && !error && data.length === 0 ? <Text color="fg.muted">No submissions found.</Text> : null}
        {data.length > 0 ? (
          <Box>
            <AdminSubmissionTable submissions={data} onSelect={setSelected} />
            <Pagination skip={skip} limit={PAGE_SIZE} total={total} onChange={setSkip} />
          </Box>
        ) : null}
      </Stack>
      <RoastDrawer submission={selected} onClose={() => setSelected(null)} />
    </PageWrapper>
  );
}
