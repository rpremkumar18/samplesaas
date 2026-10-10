import { Button, HStack, Text } from '@chakra-ui/react';

interface PaginationProps {
  skip: number;
  limit: number;
  total: number;
  onChange: (skip: number) => void;
}

export function Pagination({ skip, limit, total, onChange }: PaginationProps) {
  const page = Math.floor(skip / limit) + 1;
  const pages = Math.max(1, Math.ceil(total / limit));
  return (
    <HStack justify="space-between" mt={4}>
      <Text color="fg.muted" fontSize="sm">
        Page {page} of {pages} ({total} total)
      </Text>
      <HStack>
        <Button size="sm" variant="outline" disabled={skip === 0} onClick={() => onChange(Math.max(0, skip - limit))}>
          Previous
        </Button>
        <Button size="sm" variant="outline" disabled={page >= pages} onClick={() => onChange(skip + limit)}>
          Next
        </Button>
      </HStack>
    </HStack>
  );
}
