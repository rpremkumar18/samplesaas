import { Button, Heading, Text } from '@chakra-ui/react';
import { Link as RouterLink } from 'react-router-dom';
import { PageWrapper } from '../components/layout/PageWrapper';
import { GlassCard } from '../components/ui/GlassCard';

export default function NotFoundPage() {
  return (
    <PageWrapper>
      <GlassCard maxW="lg" mx="auto" textAlign="center">
        <Heading size="2xl">404</Heading>
        <Heading size="lg" mt={2}>
          Page not found
        </Heading>
        <Text mt={2} color="fg.muted">
          Intha page illa machan. The link may be broken or the page may have moved.
        </Text>
        <Button asChild mt={6}>
          <RouterLink to="/dashboard">Back to dashboard</RouterLink>
        </Button>
      </GlassCard>
    </PageWrapper>
  );
}
