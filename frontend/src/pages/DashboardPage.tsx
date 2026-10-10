import { Box, Button, Heading, Stack, Text } from '@chakra-ui/react';
import { Link as RouterLink } from 'react-router-dom';
import { PageWrapper } from '../components/layout/PageWrapper';
import { GlassCard } from '../components/ui/GlassCard';
import { GradientButton } from '../components/ui/GradientButton';
import { StatCards } from '../components/dashboard/StatCards';
import { RecentRoasts } from '../components/dashboard/RecentRoasts';
import { ScoreTrend } from '../components/dashboard/ScoreTrend';
import { useDashboard } from '../hooks/useDashboard';

export default function DashboardPage() {
  const { data, loading, error, reload } = useDashboard();
  const isEmpty = !loading && !error && data !== null && data.totalSubmissions === 0 && data.totalRoasts === 0;

  return (
    <PageWrapper>
      <Heading size="2xl" mb={6}>
        Dashboard
      </Heading>
      {error ? (
        <GlassCard>
          <Text mb={4} role="alert">
            {error}
          </Text>
          <Button onClick={reload}>Retry</Button>
        </GlassCard>
      ) : isEmpty ? (
        <GlassCard>
          <Heading size="lg" mb={2}>
            No roasts yet
          </Heading>
          <Text mb={4} opacity={0.8}>
            Submit your first assignment repo and get roasted.
          </Text>
          <RouterLink to="/submissions/new">
            <GradientButton>Submit an assignment</GradientButton>
          </RouterLink>
        </GlassCard>
      ) : (
        <Stack gap={6}>
          <StatCards
            loading={loading}
            totalSubmissions={data?.totalSubmissions ?? 0}
            totalRoasts={data?.totalRoasts ?? 0}
            averageScore={data?.averageScore ?? null}
            bestScore={data?.bestScore ?? null}
          />
          <Box display="grid" gridTemplateColumns={{ base: '1fr', lg: '1fr 1fr' }} gap={6}>
            <ScoreTrend loading={loading} roasts={data?.trend ?? []} />
            <RecentRoasts loading={loading} roasts={data?.recent ?? []} />
          </Box>
        </Stack>
      )}
    </PageWrapper>
  );
}
