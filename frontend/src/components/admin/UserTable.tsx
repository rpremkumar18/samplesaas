import { Badge, Button, HStack, Table } from '@chakra-ui/react';
import type { AdminUser } from '../../types';

interface UserTableProps {
  users: AdminUser[];
  onToggleActive: (user: AdminUser) => void;
  onToggleAdmin: (user: AdminUser) => void;
}

export function UserTable({ users, onToggleActive, onToggleAdmin }: UserTableProps) {
  return (
    <Table.ScrollArea>
      <Table.Root size="sm" variant="line">
        <Table.Header>
          <Table.Row>
            <Table.ColumnHeader>Email</Table.ColumnHeader>
            <Table.ColumnHeader>Name</Table.ColumnHeader>
            <Table.ColumnHeader>Status</Table.ColumnHeader>
            <Table.ColumnHeader>Role</Table.ColumnHeader>
            <Table.ColumnHeader>Joined</Table.ColumnHeader>
            <Table.ColumnHeader>Actions</Table.ColumnHeader>
          </Table.Row>
        </Table.Header>
        <Table.Body>
          {users.map((user) => (
            <Table.Row key={user.id}>
              <Table.Cell>{user.email}</Table.Cell>
              <Table.Cell>{user.full_name ?? '-'}</Table.Cell>
              <Table.Cell>
                <HStack gap={1}>
                  <Badge colorPalette={user.is_active ? 'green' : 'red'}>
                    {user.is_active ? 'Active' : 'Inactive'}
                  </Badge>
                  {user.is_verified ? <Badge colorPalette="blue">Verified</Badge> : null}
                </HStack>
              </Table.Cell>
              <Table.Cell>
                <Badge colorPalette={user.is_admin ? 'purple' : 'gray'}>
                  {user.is_admin ? 'Admin' : 'User'}
                </Badge>
              </Table.Cell>
              <Table.Cell>{new Date(user.created_at).toLocaleDateString()}</Table.Cell>
              <Table.Cell>
                <HStack gap={2}>
                  <Button size="xs" variant="outline" onClick={() => onToggleActive(user)}>
                    {user.is_active ? 'Deactivate' : 'Activate'}
                  </Button>
                  <Button size="xs" variant="outline" onClick={() => onToggleAdmin(user)}>
                    {user.is_admin ? 'Revoke admin' : 'Make admin'}
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
