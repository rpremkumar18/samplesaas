import { Alert, Button, Heading, HStack, Spinner, Stack, Text } from '@chakra-ui/react';
import { Link as RouterLink, useParams } from 'react-router-dom';
import { PageWrapper } from '../components/layout/PageWrapper';
import { GlassCard } from '../components/ui/GlassCard';
import { RoastCard } from '../components/roasts/RoastCard';
import { ScoreBadge } from '../components/roasts/ScoreBadge';
import { TipList } from '../components/roasts/TipList';
import { useRoast } from '../hooks/useRoasts';

export default function RoastPage() {
  const { submissionId } = useParams<{ submissionId: string }>();
  const id = Number(submissionId);
  const { roast, loading, error, reload } = useRoast(id);

  return (
    <PageWrapper>
      <Stack maxW="4xl" mx="auto" gap={6}>
        <HStack justify="space-between" wrap="wrap">
          <Button asChild variant="ghost">
            <RouterLink to="/submissions">Back to submissions</RouterLink>
          </Button>
          <Button asChild variant="ghost">
            <RouterLink to="/roasts">All roasts</RouterLink>
          </Button>
        </HStack>

        {loading && <Spinner size="xl" alignSelf="center" />}

        {!loading && error === 'not_ready' && (
          <GlassCard>
            <Stack gap={3}>
              <Heading size="md">Roast not ready yet</Heading>
              <Text color="gray.300">
                The roast is still cooking. Check the submission page for progress, then come back.
              </Text>
              <HStack>
                <Button asChild colorPalette="orange">
                  <RouterLink to={`/submissions/${id}`}>Go to submission</RouterLink>
                </Button>
                <Button variant="outline" onClick={() => void reload()}>
                  Retry
                </Button>
              </HStack>
            </Stack>
          </GlassCard>
        )}

        {!loading && error === 'error' && (
          <Alert.Root status="error">
            <Alert.Indicator />
            <Alert.Title>Could not load the roast.</Alert.Title>
            <Button size="sm" onClick={() => void reload()}>
              Retry
            </Button>
          </Alert.Root>
        )}

        {!loading && roast && (
          <>
            <GlassCard>
              <HStack gap={8} wrap="wrap" justify="center">
                <ScoreBadge score={roast.score} />
                <Stack flex="1" minW="240px" gap={2}>
                  <Heading size="xl">{roast.assignment_title ?? 'Your assignment'}</Heading>
                  <Text fontSize="sm" color="gray.400" wordBreak="break-all">
                    {roast.repo_url}
                  </Text>
                  {roast.summary && <Text color="gray.200">{roast.summary}</Text>}
                </Stack>
              </HStack>
            </GlassCard>
            <RoastCard roastText={roast.roast_text} />
            <GlassCard>
              <Heading size="lg" mb={4}>
                How to improve
              </Heading>
              <TipList tips={roast.tips} />
            </GlassCard>
          </>
        )}
      </Stack>
    </PageWrapper>
  );
}
