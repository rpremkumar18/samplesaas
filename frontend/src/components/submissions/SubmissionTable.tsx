import { Button, HStack, Table, Text } from '@chakra-ui/react';
import { Link } from 'react-router-dom';
import type { Submission } from '../../types';
import { StatusBadge } from './StatusBadge';

interface SubmissionTableProps {
  items: Submission[];
  onDelete: (submission: Submission) => void;
}

export function SubmissionTable({ items, onDelete }: SubmissionTableProps) {
  return (
    <Table.ScrollArea>
      <Table.Root variant="line">
        <Table.Header>
          <Table.Row>
            <Table.ColumnHeader>Repository</Table.ColumnHeader>
            <Table.ColumnHeader>Title</Table.ColumnHeader>
            <Table.ColumnHeader>Status</Table.ColumnHeader>
            <Table.ColumnHeader>Submitted</Table.ColumnHeader>
            <Table.ColumnHeader textAlign="end">Actions</Table.ColumnHeader>
          </Table.Row>
        </Table.Header>
        <Table.Body>
          {items.map((s) => (
            <Table.Row key={s.id}>
              <Table.Cell>
                <Link to={`/submissions/${s.id}`}>
                  <Text color={{ base: 'purple.600', _dark: 'purple.300' }} fontWeight="semibold">
                    {s.repo_owner}/{s.repo_name}
                  </Text>
                </Link>
              </Table.Cell>
              <Table.Cell>{s.assignment_title ?? '-'}</Table.Cell>
              <Table.Cell>
                <StatusBadge status={s.status} />
              </Table.Cell>
              <Table.Cell>{new Date(s.created_at).toLocaleString()}</Table.Cell>
              <Table.Cell>
                <HStack justify="flex-end" gap={2}>
                  <Button asChild size="xs" variant="outline">
                    <Link to={`/submissions/${s.id}`}>View</Link>
                  </Button>
                  <Button size="xs" colorPalette="red" variant="outline" onClick={() => onDelete(s)}>
                    Delete
                  </Button>
                </HStack>
              </Table.Cell>
            </Table.Row>
          ))}
        </Table.Body>
      </Table.Root>
    </Table.ScrollArea>
  );
}
