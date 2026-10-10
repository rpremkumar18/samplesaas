import type { ReactNode } from 'react';
import { Badge, Box, CloseButton, Drawer, Link, Portal, Stack, Text } from '@chakra-ui/react';
import type { AdminSubmission } from '../../types';
import { STATUS_COLORS } from './statusColors';

interface RoastDrawerProps {
  submission: AdminSubmission | null;
  onClose: () => void;
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <Box>
      <Text fontSize="xs" color="fg.muted" textTransform="uppercase">
        {label}
      </Text>
      <Text>{children}</Text>
    </Box>
  );
}

export function RoastDrawer({ submission, onClose }: RoastDrawerProps) {
  return (
    <Drawer.Root
      open={submission !== null}
      onOpenChange={(e) => {
        if (!e.open) onClose();
      }}
      size="md"
    >
      <Portal>
        <Drawer.Backdrop />
        <Drawer.Positioner>
          <Drawer.Content>
            <Drawer.Header>
              <Drawer.Title>
                {submission ? (submission.assignment_title ?? `Submission #${submission.id}`) : ''}
              </Drawer.Title>
            </Drawer.Header>
            <Drawer.Body>
              {submission ? (
                <Stack gap={4}>
                  <Badge alignSelf="flex-start" colorPalette={STATUS_COLORS[submission.status]}>
                    {submission.status}
                  </Badge>
                  <Field label="User">{submission.user_email}</Field>
                  <Field label="Repository">
                    <Link href={submission.repo_url} target="_blank" rel="noopener noreferrer" color="purple.400">
                      {submission.repo_url}
                    </Link>
                  </Field>
                  <Field label="Score">{submission.score === null ? 'Not scored' : submission.score}</Field>
                  <Field label="Created">{new Date(submission.created_at).toLocaleString()}</Field>
                  <Field label="Updated">{new Date(submission.updated_at).toLocaleString()}</Field>
                  {submission.error_message ? <Field label="Error">{submission.error_message}</Field> : null}
                  <Text color="fg.muted" fontSize="sm">
                    The roast text is only visible to the learner who submitted this assignment.
                  </Text>
                </Stack>
              ) : null}
            </Drawer.Body>
            <Drawer.CloseTrigger asChild>
              <CloseButton size="sm" />
            </Drawer.CloseTrigger>
          </Drawer.Content>
        </Drawer.Positioner>
      </Portal>
    </Drawer.Root>
  );
}
