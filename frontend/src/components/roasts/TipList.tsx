import { Badge, Box, Code, Heading, HStack, Stack, Text } from '@chakra-ui/react';
import type { ImprovementTip, TipCategory } from '../../types';

const CATEGORY_META: Record<TipCategory, { label: string; palette: string }> = {
  structure: { label: 'Structure', palette: 'blue' },
  naming: { label: 'Naming', palette: 'purple' },
  bugs: { label: 'Bugs', palette: 'red' },
  security: { label: 'Security', palette: 'orange' },
  readability: { label: 'Readability', palette: 'teal' },
  best_practices: { label: 'Best Practices', palette: 'green' },
};

const ORDER: TipCategory[] = ['bugs', 'security', 'structure', 'naming', 'readability', 'best_practices'];

export function TipList({ tips }: { tips: ImprovementTip[] }) {
  if (tips.length === 0) {
    return <Text color="fg.muted">No tips this time. Suspiciously clean!</Text>;
  }
  const groups = ORDER.map((cat) => ({ cat, items: tips.filter((t) => t.category === cat) })).filter(
    (g) => g.items.length > 0,
  );
  return (
    <Stack gap={6}>
      {groups.map(({ cat, items }) => (
        <Box key={cat}>
          <Badge colorPalette={CATEGORY_META[cat].palette} mb={3} fontSize="sm" px={3} py={1}>
            {CATEGORY_META[cat].label}
          </Badge>
          <Stack gap={3}>
            {items.map((tip) => (
              <Box key={tip.id} p={4} rounded="xl" bg="bg.subtle" borderWidth="1px" borderColor="border">
                <HStack justify="space-between" align="start" wrap="wrap" gap={2}>
                  <Heading size="sm">{tip.title}</Heading>
                  {tip.file_path && <Code fontSize="xs">{tip.file_path}</Code>}
                </HStack>
                <Text mt={2} color="fg.muted" whiteSpace="pre-wrap">
                  {tip.description}
                </Text>
              </Box>
            ))}
          </Stack>
        </Box>
      ))}
    </Stack>
  );
}
