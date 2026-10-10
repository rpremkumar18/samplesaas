import { Box, SimpleGrid, Skeleton, Text } from '@chakra-ui/react';
import { GlassCard } from '../ui/GlassCard';

interface StatCardsProps {
  loading: boolean;
  totalSubmissions: number;
  totalRoasts: number;
  averageScore: number | null;
  bestScore: number | null;
}

function fmt(n: number | null): string {
  return n === null ? '-' : n.toFixed(1);
}

export function StatCards({ loading, totalSubmissions, totalRoasts, averageScore, bestScore }: StatCardsProps) {
  const stats: { label: string; value: string }[] = [
    { label: 'Total submissions', value: String(totalSubmissions) },
    { label: 'Roasts received', value: String(totalRoasts) },
    { label: 'Average score', value: fmt(averageScore) },
    { label: 'Best score', value: fmt(bestScore) },
  ];
  return (
    <SimpleGrid columns={{ base: 1, sm: 2, lg: 4 }} gap={4}>
      {stats.map((s) => (
        <GlassCard key={s.label}>
          <Text fontSize="sm" opacity={0.7}>
            {s.label}
          </Text>
          <Box mt={1}>
            {loading ? (
              <Skeleton h="36px" w="80px" data-testid="stat-skeleton" />
            ) : (
              <Text fontSize="3xl" fontWeight="bold">
                {s.value}
              </Text>
            )}
          </Box>
        </GlassCard>
      ))}
    </SimpleGrid>
  );
}
