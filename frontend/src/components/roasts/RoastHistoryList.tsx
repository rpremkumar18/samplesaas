import { Box, Heading, HStack, Text } from '@chakra-ui/react';
import { Link as RouterLink } from 'react-router-dom';
import { AnimatedList } from '../ui/AnimatedList';
import { GlassCard } from '../ui/GlassCard';
import { ScoreBadge } from './ScoreBadge';
import type { Roast } from '../../types';

const SNIPPET_LENGTH = 140;

function snippet(text: string | null): string {
  if (!text) return '';
  return text.length > SNIPPET_LENGTH ? `${text.slice(0, SNIPPET_LENGTH)}...` : text;
}

export function RoastHistoryList({ roasts }: { roasts: Roast[] }) {
  return (
    <AnimatedList>
      {roasts.map((r) => (
        <RouterLink key={r.id} to={`/roasts/${r.submission_id}`}>
          <GlassCard mb={4}>
            <HStack gap={4} align="center">
              <ScoreBadge score={r.score} size="sm" />
              <Box minW={0}>
                <Heading size="md" truncate>
                  {r.assignment_title ?? r.repo_url}
                </Heading>
                <Text fontSize="xs" color="gray.400">
                  {new Date(r.created_at).toLocaleDateString()}
                </Text>
                <Text mt={1} color="gray.300">
                  {snippet(r.summary)}
                </Text>
              </Box>
            </HStack>
          </GlassCard>
        </RouterLink>
      ))}
    </AnimatedList>
  );
}
