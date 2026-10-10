import { Button, Heading, HStack, Spinner, Text, VStack } from '@chakra-ui/react';
import { Link, useParams } from 'react-router-dom';
import { PageWrapper } from '../components/layout/PageWrapper';
import { GlassCard } from '../components/ui/GlassCard';
import { GradientButton } from '../components/ui/GradientButton';
import { StatusBadge } from '../components/submissions/StatusBadge';
import { StatusTracker } from '../components/submissions/StatusTracker';
import { useSubmissionPolling } from '../hooks/useSubmissionPolling';

export default function SubmissionDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { submission, loading, error, retrying, timedOut, refresh, retry } = useSubmissionPolling(Number(id));

  return (
    <PageWrapper>
      <Button asChild variant="ghost" mb={4}>
        <Link to="/submissions">Back to submissions</Link>
      </Button>
      {loading && <Spinner />}
      {error && (
        <Text color="red.300" mb={4}>
          {error}
        </Text>
      )}
      {submission && (
        <GlassCard maxW="3xl">
          <VStack align="stretch" gap={5}>
            <HStack justify="space-between" wrap="wrap">
              <Heading size="xl">
                {submission.repo_owner}/{submission.repo_name}
              </Heading>
              <StatusBadge status={submission.status} />
            </HStack>
            {submission.assignment_title && <Text color="gray.300">{submission.assignment_title}</Text>}
            <Text color="gray.400" fontSize="sm">
              {submission.repo_url}
            </Text>
            <StatusTracker status={submission.status} timedOut={timedOut} onRefresh={refresh} />
            {submission.status === 'completed' && (
              <Link to={`/roasts/${submission.id}`}>
                <GradientButton>View your roast</GradientButton>
              </Link>
            )}
            {submission.status === 'failed' && (
              <VStack align="stretch" gap={3}>
                <Text color="red.300">{submission.error_message ?? 'The analysis failed for an unknown reason.'}</Text>
                <GradientButton onClick={() => void retry()} disabled={retrying} opacity={retrying ? 0.6 : 1}>
                  {retrying ? 'Retrying...' : 'Retry'}
                </GradientButton>
              </VStack>
            )}
          </VStack>
        </GlassCard>
      )}
    </PageWrapper>
  );
}
