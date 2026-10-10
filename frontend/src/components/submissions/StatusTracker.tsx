import { Box, Button, HStack, Spinner, Text, VStack } from '@chakra-ui/react';
import { useEffect, useState } from 'react';
import type { SubmissionStatus } from '../../types';

const STEPS: { key: SubmissionStatus; label: string }[] = [
  { key: 'pending', label: 'Queued' },
  { key: 'fetching', label: 'Fetching repo' },
  { key: 'analyzing', label: 'Analyzing code' },
  { key: 'completed', label: 'Roast ready' },
];

const QUIPS: Record<string, string[]> = {
  pending: ['Waiting in line behind other questionable code...', 'Warming up the roasting oven...'],
  fetching: ['Cloning your repo and judging the folder structure...', 'Counting your TODO comments...'],
  analyzing: [
    'Reading your commit messages. Oh dear.',
    'Looking for variables named "temp2"...',
    'Sharpening the sarcasm...',
    'Consulting the code gods. They are not impressed.',
  ],
};

function stepIndex(status: SubmissionStatus): number {
  if (status === 'failed') return 0;
  return STEPS.findIndex((s) => s.key === status);
}

interface StatusTrackerProps {
  status: SubmissionStatus;
  /** Polling gave up while the job is still active. */
  timedOut?: boolean;
  onRefresh?: () => void;
}

export function StatusTracker({ status, timedOut = false, onRefresh }: StatusTrackerProps) {
  const [quipIdx, setQuipIdx] = useState(0);
  const active = status === 'pending' || status === 'fetching' || status === 'analyzing';

  useEffect(() => {
    if (!active) return undefined;
    const t = window.setInterval(() => setQuipIdx((i) => i + 1), 3500);
    return () => window.clearInterval(t);
  }, [active]);

  const current = stepIndex(status);
  const quips = QUIPS[status] ?? [];
  const quip = quips.length > 0 ? quips[quipIdx % quips.length] : '';

  return (
    <VStack align="stretch" gap={5}>
      <HStack gap={4} wrap="wrap">
        {STEPS.map((step, i) => {
          const failed = status === 'failed';
          const done = !failed && (i < current || status === 'completed');
          const isCurrent = !failed && i === current;
          return (
            <HStack key={step.key} gap={2}>
              <Box w={3} h={3} rounded="full" bg={done ? 'green.400' : isCurrent ? 'purple.400' : 'border.emphasized'} />
              <Text fontSize="sm" color={isCurrent || done ? 'fg' : 'fg.muted'} fontWeight={isCurrent ? 'bold' : 'normal'}>
                {step.label}
              </Text>
            </HStack>
          );
        })}
      </HStack>
      {active && timedOut && (
        <VStack align="stretch" gap={2}>
          <Text color={{ base: 'orange.600', _dark: 'orange.300' }}>
            This is taking longer than expected. The analysis may be stuck; refresh to check again.
          </Text>
          {onRefresh && (
            <Button size="sm" variant="outline" alignSelf="flex-start" onClick={onRefresh}>
              Refresh status
            </Button>
          )}
        </VStack>
      )}
      {active && !timedOut && (
        <HStack gap={3}>
          <Spinner size="sm" color={{ base: 'purple.600', _dark: 'purple.300' }} />
          <Text color="fg.muted">{quip}</Text>
        </HStack>
      )}
    </VStack>
  );
}
