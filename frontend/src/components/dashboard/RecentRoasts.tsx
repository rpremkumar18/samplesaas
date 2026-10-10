import { Box, Flex, Heading, Skeleton, Stack, Text } from '@chakra-ui/react';
import { Link as RouterLink } from 'react-router-dom';
import { GlassCard } from '../ui/GlassCard';
import type { Roast } from '../../types';

interface RecentRoastsProps {
  loading: boolean;
  roasts: Roast[];
}

export function RecentRoasts({ loading, roasts }: RecentRoastsProps) {
  return (
    <GlassCard>
      <Heading size="md" mb={4}>
        Recent roasts
      </Heading>
      <Stack gap={3}>
        {loading
          ? [0, 1, 2].map((i) => <Skeleton key={i} h="56px" rounded="lg" />)
          : roasts.map((r) => (
              <RouterLink key={r.id} to={`/roasts/${r.submission_id}`}>
                <Flex
                  justify="space-between"
                  align="center"
                  gap={4}
                  p={3}
                  rounded="lg"
                  bg="whiteAlpha.100"
                  _hover={{ bg: 'whiteAlpha.200' }}
                >
                  <Box minW={0}>
                    <Text fontWeight="semibold" truncate>
                      {r.assignment_title ?? r.repo_url ?? `Submission #${r.submission_id}`}
                    </Text>
                    <Text fontSize="sm" opacity={0.7} truncate>
                      {r.summary ?? new Date(r.created_at).toLocaleDateString()}
                    </Text>
                  </Box>
                  <Text fontSize="xl" fontWeight="bold" flexShrink={0}>
                    {r.score}
                  </Text>
                </Flex>
              </RouterLink>
            ))}
      </Stack>
    </GlassCard>
  );
}
