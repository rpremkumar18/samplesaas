import { Button, Heading, HStack, Spinner, Text } from '@chakra-ui/react';
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { PageWrapper } from '../components/layout/PageWrapper';
import { GlassCard } from '../components/ui/GlassCard';
import { SubmissionTable } from '../components/submissions/SubmissionTable';
import { useSubmissions } from '../hooks/useSubmissions';
import { extractErrorMessage } from '../services/submissionService';
import type { Submission } from '../types';

export default function SubmissionsPage() {
  const { items, total, loading, error, remove } = useSubmissions();
  const [pending, setPending] = useState<Submission | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const confirmDelete = async (): Promise<void> => {
    if (!pending) return;
    setDeleting(true);
    try {
      await remove(pending.id);
      setActionError(null);
    } catch (e: unknown) {
      setActionError(extractErrorMessage(e, 'Could not delete submission.'));
    } finally {
      setDeleting(false);
      setPending(null);
    }
  };

  return (
    <PageWrapper>
      <HStack justify="space-between" mb={6} wrap="wrap">
        <Heading size="2xl">My submissions ({total})</Heading>
        <Button asChild colorPalette="purple">
          <Link to="/submissions/new">New submission</Link>
        </Button>
      </HStack>
      {actionError && (
        <Text color="red.300" mb={4}>
          {actionError}
        </Text>
      )}
      {pending && (
        <GlassCard mb={4}>
          <Text mb={3}>
            Delete {pending.repo_owner}/{pending.repo_name}? This also removes its roast.
          </Text>
          <HStack gap={3}>
            <Button colorPalette="red" onClick={() => void confirmDelete()} disabled={deleting}>
              {deleting ? 'Deleting...' : 'Yes, delete'}
            </Button>
            <Button variant="outline" onClick={() => setPending(null)} disabled={deleting}>
              Cancel
            </Button>
          </HStack>
        </GlassCard>
      )}
      {loading && <Spinner />}
      {error && <Text color="red.300">{error}</Text>}
      {!loading && !error && items.length === 0 && (
        <Text color="gray.400">Nothing here yet. Submit a repo and get roasted!</Text>
      )}
      {items.length > 0 && (
        <GlassCard>
          <SubmissionTable items={items} onDelete={setPending} />
        </GlassCard>
      )}
    </PageWrapper>
  );
}
