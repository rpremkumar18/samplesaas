import { Badge, Button, Link, Table, Text } from '@chakra-ui/react';
import type { AdminSubmission } from '../../types';
import { STATUS_COLORS } from './statusColors';

interface AdminSubmissionTableProps {
  submissions: AdminSubmission[];
  onSelect: (submission: AdminSubmission) => void;
}

export function AdminSubmissionTable({ submissions, onSelect }: AdminSubmissionTableProps) {
  return (
    <Table.ScrollArea>
      <Table.Root size="sm" variant="line">
        <Table.Header>
          <Table.Row>
            <Table.ColumnHeader>Assignment</Table.ColumnHeader>
            <Table.ColumnHeader>User</Table.ColumnHeader>
            <Table.ColumnHeader>Repository</Table.ColumnHeader>
            <Table.ColumnHeader>Status</Table.ColumnHeader>
            <Table.ColumnHeader>Score</Table.ColumnHeader>
            <Table.ColumnHeader>Created</Table.ColumnHeader>
            <Table.ColumnHeader />
          </Table.Row>
        </Table.Header>
        <Table.Body>
          {submissions.map((s) => (
            <Table.Row key={s.id}>
              <Table.Cell>{s.assignment_title ?? `Submission #${s.id}`}</Table.Cell>
              <Table.Cell>{s.user_email}</Table.Cell>
              <Table.Cell>
                <Link href={s.repo_url} target="_blank" rel="noopener noreferrer" color="purple.400">
                  {s.repo_owner && s.repo_name ? `${s.repo_owner}/${s.repo_name}` : s.repo_url}
                </Link>
              </Table.Cell>
              <Table.Cell>
                <Badge colorPalette={STATUS_COLORS[s.status]}>{s.status}</Badge>
              </Table.Cell>
              <Table.Cell>{s.score === null ? <Text color="fg.muted">-</Text> : s.score}</Table.Cell>
              <Table.Cell>{new Date(s.created_at).toLocaleDateString()}</Table.Cell>
              <Table.Cell>
                <Button size="xs" variant="ghost" onClick={() => onSelect(s)}>
                  Details
                </Button>
              </Table.Cell>
            </Table.Row>
          ))}
        </Table.Body>
      </Table.Root>
    </Table.ScrollArea>
  );
}
