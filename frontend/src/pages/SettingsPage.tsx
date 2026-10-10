import { Heading, Stack, Switch, Text } from '@chakra-ui/react';
import { PageWrapper } from '../components/layout/PageWrapper';
import { GlassCard } from '../components/ui/GlassCard';
import { useColorMode } from '../hooks/useColorMode';

export default function SettingsPage() {
  const { mode, setMode } = useColorMode();
  return (
    <PageWrapper>
      <Heading size="2xl" mb={6}>
        Settings
      </Heading>
      <GlassCard maxW="lg">
        <Stack gap={4}>
          <Heading size="md">Appearance</Heading>
          <Switch.Root
            checked={mode === 'dark'}
            onCheckedChange={(e) => setMode(e.checked ? 'dark' : 'light')}
          >
            <Switch.HiddenInput />
            <Switch.Control>
              <Switch.Thumb />
            </Switch.Control>
            <Switch.Label>Dark mode</Switch.Label>
          </Switch.Root>
          <Text fontSize="sm" opacity={0.7}>
            Your preference is saved in this browser.
          </Text>
        </Stack>
      </GlassCard>
    </PageWrapper>
  );
}
