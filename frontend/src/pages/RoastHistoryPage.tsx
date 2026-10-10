import { Alert, Button, Heading, Spinner, Stack, Text } from '@chakra-ui/react';
import { PageWrapper } from '../components/layout/PageWrapper';
import { RoastHistoryList } from '../components/roasts/RoastHistoryList';
import { useRoastHistory } from '../hooks/useRoasts';

export default function RoastHistoryPage() {
  const { roasts, total, loading, error, reload } = useRoastHistory();

  return (
    <PageWrapper>
      <Stack maxW="4xl" mx="auto" gap={6}>
        <Heading size="2xl">Roast History</Heading>
        {loading && <Spinner size="xl" alignSelf="center" />}
        {!loading && error && (
          <Alert.Root status="error">
            <Alert.Indicator />
            <Alert.Title>Could not load roasts.</Alert.Title>
            <Button size="sm" onClick={() => void reload()}>
              Retry
            </Button>
          </Alert.Root>
        )}
        {!loading && !error && roasts.length === 0 && (
          <Text color="fg.muted">No roasts yet. Submit an assignment to get roasted!</Text>
        )}
        {!loading && !error && roasts.length > 0 && (
          <>
            <Text color="fg.muted">{total} roast(s)</Text>
            <RoastHistoryList roasts={roasts} />
          </>
        )}
      </Stack>
    </PageWrapper>
  );
}
