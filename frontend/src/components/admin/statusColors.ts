import type { SubmissionStatus } from '../../types';

export const STATUS_COLORS: Record<SubmissionStatus, string> = {
  pending: 'gray',
  fetching: 'blue',
  analyzing: 'orange',
  completed: 'green',
  failed: 'red',
};
