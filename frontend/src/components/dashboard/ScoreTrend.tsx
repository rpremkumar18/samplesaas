import { Box, Heading, Skeleton, Text, chakra } from '@chakra-ui/react';
import { GlassCard } from '../ui/GlassCard';
import type { Roast } from '../../types';

interface ScoreTrendProps {
  loading: boolean;
  roasts: Roast[];
}

const W = 600;
const H = 200;
const PAD = 24;

export function ScoreTrend({ loading, roasts }: ScoreTrendProps) {
  const scores = roasts.map((r) => r.score);
  const max = Math.max(10, ...scores);
  const x = (i: number): number =>
    scores.length === 1 ? W / 2 : PAD + (i * (W - 2 * PAD)) / (scores.length - 1);
  const y = (s: number): number => H - PAD - (s / max) * (H - 2 * PAD);
  const points = scores.map((s, i) => `${x(i)},${y(s)}`).join(' ');

  return (
    <GlassCard>
      <Heading size="md" mb={4}>
        Score trend
      </Heading>
      {loading ? (
        <Skeleton h="200px" rounded="lg" />
      ) : scores.length < 2 ? (
        <Text opacity={0.7}>Complete at least two roasts to see your trend.</Text>
      ) : (
        <Box>
          <chakra.svg
            viewBox={`0 0 ${W} ${H}`}
            w="100%"
            h="auto"
            role="img"
            aria-label="Score trend from oldest to newest roast"
          >
            <chakra.line x1={PAD} y1={H - PAD} x2={W - PAD} y2={H - PAD} stroke="currentColor" opacity={0.3} />
            <chakra.polyline points={points} fill="none" stroke="#a855f7" strokeWidth={3} strokeLinejoin="round" />
            {scores.map((s, i) => (
              <chakra.circle key={roasts[i].id} cx={x(i)} cy={y(s)} r={4} fill="#ec4899">
                <title>{`Score ${s}`}</title>
              </chakra.circle>
            ))}
          </chakra.svg>
          <Text fontSize="xs" opacity={0.6}>
            Oldest to newest, scale 0 to {max}
          </Text>
        </Box>
      )}
    </GlassCard>
  );
}
