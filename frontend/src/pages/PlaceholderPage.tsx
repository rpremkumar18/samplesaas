import { Heading, Text } from '@chakra-ui/react';
import { PageWrapper } from '../components/layout/PageWrapper';
import { GlassCard } from '../components/ui/GlassCard';

interface PlaceholderPageProps {
  title: string;
  route: string;
}

export function PlaceholderPage({ title, route }: PlaceholderPageProps) {
  return (
    <PageWrapper>
      <GlassCard maxW="lg" mx="auto">
        <Heading size="lg">{title}</Heading>
        <Text mt={2} color="fg.muted">
          Route {route} - placeholder
        </Text>
      </GlassCard>
    </PageWrapper>
  );
}
