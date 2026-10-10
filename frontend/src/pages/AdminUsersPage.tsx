import { useEffect, useState } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import { Alert, Box, Button, Dialog, Heading, HStack, Input, Portal, Spinner, Stack, Text } from '@chakra-ui/react';
import { PageWrapper } from '../components/layout/PageWrapper';
import { UserTable } from '../components/admin/UserTable';
import { Pagination } from '../components/admin/Pagination';
import { useAdminUsers } from '../hooks/useAdmin';
import type { AdminUser, AdminUserUpdate } from '../types';

const PAGE_SIZE = 20;

interface PendingChange {
  user: AdminUser;
  update: AdminUserUpdate;
  message: string;
}

export default function AdminUsersPage() {
  const [searchInput, setSearchInput] = useState('');
  const [search, setSearch] = useState('');
  const [skip, setSkip] = useState(0);
  const [pending, setPending] = useState<PendingChange | null>(null);
  const [saving, setSaving] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const { data, total, loading, error, reload, updateUser } = useAdminUsers({ skip, limit: PAGE_SIZE, search });

  useEffect(() => {
    const t = setTimeout(() => {
      setSearch(searchInput.trim());
      setSkip(0);
    }, 300);
    return () => clearTimeout(t);
  }, [searchInput]);

  const requestChange = (user: AdminUser, update: AdminUserUpdate, action: string) => {
    setActionError(null);
    setPending({ user, update, message: `${action} ${user.email}?` });
  };

  const confirm = async () => {
    if (!pending) return;
    setSaving(true);
    const err = await updateUser(pending.user.id, pending.update);
    setSaving(false);
    setPending(null);
    if (err) setActionError(err);
  };

  return (
    <PageWrapper>
      <Stack gap={6} maxW="6xl" mx="auto">
        <HStack justify="space-between" wrap="wrap">
          <Heading size="2xl">Users</Heading>
          <Button asChild variant="outline">
            <RouterLink to="/admin">Back to dashboard</RouterLink>
          </Button>
        </HStack>
        <Input
          placeholder="Search by email or name"
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          maxW="md"
        />
        {actionError ? (
          <Alert.Root status="error">
            <Alert.Indicator />
            <Alert.Title>{actionError}</Alert.Title>
          </Alert.Root>
        ) : null}
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
        {!loading && !error && data.length === 0 ? <Text color="fg.muted">No users found.</Text> : null}
        {data.length > 0 ? (
          <Box>
            <UserTable
              users={data}
              onToggleActive={(u) =>
                requestChange(u, { is_active: !u.is_active }, u.is_active ? 'Deactivate' : 'Activate')
              }
              onToggleAdmin={(u) =>
                requestChange(u, { is_admin: !u.is_admin }, u.is_admin ? 'Revoke admin from' : 'Grant admin to')
              }
            />
            <Pagination skip={skip} limit={PAGE_SIZE} total={total} onChange={setSkip} />
          </Box>
        ) : null}
      </Stack>

      <Dialog.Root
        open={pending !== null}
        onOpenChange={(e) => {
          if (!e.open) setPending(null);
        }}
        role="alertdialog"
      >
        <Portal>
          <Dialog.Backdrop />
          <Dialog.Positioner>
            <Dialog.Content>
              <Dialog.Header>
                <Dialog.Title>Confirm change</Dialog.Title>
              </Dialog.Header>
              <Dialog.Body>
                <Text>{pending?.message}</Text>
              </Dialog.Body>
              <Dialog.Footer>
                <Button variant="outline" onClick={() => setPending(null)} disabled={saving}>
                  Cancel
                </Button>
                <Button colorPalette="purple" onClick={() => void confirm()} loading={saving}>
                  Confirm
                </Button>
              </Dialog.Footer>
            </Dialog.Content>
          </Dialog.Positioner>
        </Portal>
      </Dialog.Root>
    </PageWrapper>
  );
}
