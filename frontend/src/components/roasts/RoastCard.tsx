import { Heading, Stack, Text } from '@chakra-ui/react';
import { GlassCard } from '../ui/GlassCard';

export function RoastCard({ roastText }: { roastText: string }) {
  return (
    <GlassCard p={{ base: 5, md: 8 }} borderColor="orange.400">
      <Stack gap={4}>
        <Heading size="lg">The Roast</Heading>
        <Text fontSize={{ base: 'md', md: 'lg' }} lineHeight="1.8" whiteSpace="pre-wrap" wordBreak="break-word">
          {roastText}
        </Text>
      </Stack>
    </GlassCard>
  );
}
