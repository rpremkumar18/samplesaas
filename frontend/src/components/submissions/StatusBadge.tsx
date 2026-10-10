import { Badge } from '@chakra-ui/react';
import type { SubmissionStatus } from '../../types';

const CONFIG: Record<SubmissionStatus, { label: string; palette: string }> = {
  pending: { label: 'Pending', palette: 'gray' },
  fetching: { label: 'Fetching repo', palette: 'blue' },
  analyzing: { label: 'Analyzing', palette: 'purple' },
  completed: { label: 'Completed', palette: 'green' },
  failed: { label: 'Failed', palette: 'red' },
};

export function StatusBadge({ status }: { status: SubmissionStatus }) {
  const { label, palette } = CONFIG[status];
  return (
    <Badge colorPalette={palette} variant="subtle" rounded="full" px={3} py={1}>
      {label}
    </Badge>
  );
}
